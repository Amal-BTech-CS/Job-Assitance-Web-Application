"""
Unit tests for the multi-turn conversation logic added to the chatbot:
planner classification (smalltalk / followup / agents), the condenser
(reference resolution), and the followup reformat path.

These mock llm.invoke() directly, so they run in seconds, need no Groq
calls, and don't touch FAISS/Qdrant. They do NOT test retrieval quality
or real resume/job content -- that needs your actual data and is covered
by the manual test script instead.

Run with:
    python manage.py test accounts.ai.chatbot.tests
"""

import json
from unittest.mock import patch, MagicMock

from django.test import TestCase

from accounts.ai.chatbot.core import resources
from accounts.ai.chatbot.planner.planner_agent import create_plan
from accounts.ai.chatbot.langgraph_workflow.nodes import (
    condense_node,
    followup_node,
    route_after_planner,
)


def _fake_response(text):
    """Mimics the object llm.invoke() returns -- just needs .content"""
    mock = MagicMock()
    mock.content = text
    return mock


class PlannerClassificationTests(TestCase):

    def test_smalltalk_fastpath_skips_llm_call(self):
        with patch.object(resources.llm, "invoke") as mock_invoke:
            plan = create_plan("hello")
            self.assertEqual(plan["type"], "smalltalk")
            mock_invoke.assert_not_called()

    def test_bare_ack_with_no_history_is_smalltalk_no_llm_call(self):
        with patch.object(resources.llm, "invoke") as mock_invoke:
            plan = create_plan("ok")
            self.assertEqual(plan["type"], "smalltalk")
            mock_invoke.assert_not_called()

    def test_bare_ack_with_history_is_evaluated_by_the_llm(self):
        # This is the exact bug the last patch fixed: "ok" right after a
        # real answer must NOT be force-matched to the local regex --
        # it needs to reach the planner LLM so it can become "followup".
        history = [
            {"role": "user", "content": "Give me a 3 month roadmap"},
            {"role": "assistant", "content": "1. Learn X 2. Build Y 3. Apply"},
        ]
        with patch.object(resources.llm, "invoke") as mock_invoke:
            mock_invoke.return_value = _fake_response(
                json.dumps({"agents": [], "type": "followup"})
            )
            plan = create_plan("ok", history=history)
            mock_invoke.assert_called_once()
            self.assertEqual(plan["type"], "followup")

    def test_json_wrapped_in_markdown_fence_is_still_parsed(self):
        with patch.object(resources.llm, "invoke") as mock_invoke:
            mock_invoke.return_value = _fake_response(
                '```json\n{"agents": ["CAREER"], "type": "agents"}\n```'
            )
            plan = create_plan("what should I learn next?")
            self.assertEqual(plan["agents"], ["CAREER"])
            self.assertEqual(plan["type"], "agents")

    def test_malformed_llm_response_falls_back_gracefully(self):
        with patch.object(resources.llm, "invoke") as mock_invoke:
            mock_invoke.return_value = _fake_response("not valid json at all")
            plan = create_plan("what should I learn next?")
            self.assertEqual(plan["agents"], ["CAREER"])
            self.assertEqual(plan["type"], "agents")

    def test_smalltalk_misclassification_of_real_question_is_overridden(self):
        # Reproduces the bug seen in manual testing: the planner LLM
        # sometimes misclassifies a genuine ATS/career question as
        # smalltalk (often after a preceding smalltalk turn biases it).
        # The keyword safety net should catch this and reroute to CAREER
        # instead of silently returning a canned greeting.
        with patch.object(resources.llm, "invoke") as mock_invoke:
            mock_invoke.return_value = _fake_response(
                json.dumps({"agents": [], "type": "smalltalk"})
            )
            plan = create_plan("What's my ATS score for the MIS role?")
            self.assertEqual(plan["type"], "agents")
            self.assertIn("CAREER", plan["agents"])

    def test_pure_courtesy_smalltalk_is_not_overridden(self):
        # "career" appears in this sentence, but it's a thank-you, not a
        # real question -- the safety net must not promote it.
        with patch.object(resources.llm, "invoke") as mock_invoke:
            mock_invoke.return_value = _fake_response(
                json.dumps({"agents": [], "type": "smalltalk"})
            )
            plan = create_plan("thanks for the career advice!")
            self.assertEqual(plan["type"], "smalltalk")


class RouterTests(TestCase):

    def test_routes_smalltalk(self):
        state = {"plan": {"type": "smalltalk"}}
        self.assertEqual(route_after_planner(state), "smalltalk")

    def test_routes_followup(self):
        state = {"plan": {"type": "followup"}}
        self.assertEqual(route_after_planner(state), "followup")

    def test_routes_agents_to_condenser(self):
        state = {"plan": {"type": "agents", "agents": ["CAREER"]}}
        self.assertEqual(route_after_planner(state), "condenser")


class FollowupNodeTests(TestCase):

    def test_reformats_last_assistant_answer_without_regenerating(self):
        history = [
            {"role": "user", "content": "Give me a roadmap"},
            {"role": "assistant", "content": "1. A 2. B 3. C 4. D 5. E 6. F"},
        ]
        state = {"question": "just give me 5 points", "history": history}

        with patch.object(resources.llm, "invoke") as mock_invoke:
            mock_invoke.return_value = _fake_response("1. A 2. B 3. C 4. D 5. E")
            result = followup_node(state)

        mock_invoke.assert_called_once()

        # The previous answer must actually be in the prompt sent to the
        # LLM -- otherwise this is regenerating, not reformatting.
        sent_prompt = mock_invoke.call_args[0][0]
        self.assertIn("1. A 2. B 3. C 4. D 5. E 6. F", sent_prompt)

        self.assertEqual(
            result["results"]["__followup__"],
            "1. A 2. B 3. C 4. D 5. E",
        )

    def test_no_prior_answer_returns_clarifying_message_not_crash(self):
        state = {"question": "just give me 5 points", "history": []}
        result = followup_node(state)
        self.assertIn("__followup__", result["results"])
        self.assertNotIn("Traceback", result["results"]["__followup__"])


class CondenseNodeTests(TestCase):

    def test_no_history_skips_llm_call(self):
        state = {"question": "what jobs match my resume?", "history": []}
        with patch.object(resources.llm, "invoke") as mock_invoke:
            result = condense_node(state)
            mock_invoke.assert_not_called()
        self.assertEqual(
            result["standalone_question"], "what jobs match my resume?"
        )

    def test_resolves_reference_using_history(self):
        history = [
            {"role": "user", "content": "What jobs match my resume?"},
            {
                "role": "assistant",
                "content": "1) Backend Dev at Acme  2) ML Engineer at Globex",
            },
        ]
        state = {
            "question": "tell me more about the second one",
            "history": history,
        }

        with patch.object(resources.llm, "invoke") as mock_invoke:
            mock_invoke.return_value = _fake_response(
                "Tell me more about the ML Engineer role at Globex"
            )
            result = condense_node(state)

        mock_invoke.assert_called_once()
        self.assertIn("Globex", result["standalone_question"])


class HistoryFilterTests(TestCase):

    def test_smalltalk_turns_are_dropped(self):
        from accounts.ai.chatbot.chatbot import _filter_informative_history

        history = [
            {"role": "user", "content": "ok"},
            {
                "role": "assistant",
                "content": "Hi there! Ask me anything about your resume.",
                "type": "smalltalk",
            },
            {"role": "user", "content": "give me a roadmap"},
            {"role": "assistant", "content": "1. A 2. B 3. C", "type": "agents"},
        ]
        filtered = _filter_informative_history(history)

        # User turns always kept; only the smalltalk assistant turn is dropped
        self.assertEqual(len(filtered), 3)
        self.assertNotIn(
            "Ask me anything",
            " ".join(t["content"] for t in filtered),
        )

    def test_followup_turns_are_kept(self):
        from accounts.ai.chatbot.chatbot import _filter_informative_history

        history = [
            {"role": "user", "content": "just give me 5 points"},
            {"role": "assistant", "content": "1. A 2. B 3. C 4. D 5. E", "type": "followup"},
        ]
        filtered = _filter_informative_history(history)
        self.assertEqual(len(filtered), 2)