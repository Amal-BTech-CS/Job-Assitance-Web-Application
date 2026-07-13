import json
import logging

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from accounts.ai.chatbot.chatbot import ask

logger = logging.getLogger(__name__)

# Number of past turns (user + assistant messages combined) kept in the
# session as context for the planner/condenser. 6 = last 3 exchanges —
# enough for follow-ups without letting the session payload or the
# planner prompt grow unbounded.
HISTORY_WINDOW = 6


@login_required
@never_cache
def chatbot_page(request):
    """
    Renders the AI Career Assistant chat UI.
    Only accessible to logged-in jobseekers.
    """
    if request.user.user_type != "jobseeker":
        return redirect("home")

    return render(request, "accounts/chatbot.html")


@login_required
@require_POST
def chat_api(request):
    """
    JSON endpoint called by the chatbot frontend.

    Expects:  POST { "message": "..." }
    Returns:  { "answer": "..." } or { "error": "..." }
    """
    try:
        body = json.loads(request.body)
        message = body.get("message", "").strip()

        if not message:
            return JsonResponse(
                {"error": "Please type a message."},
                status=400
            )

        history = request.session.get("chat_history", [])

        result = ask(request.user, message, history=history)
        answer = result["answer"]
        plan_type = result["plan_type"]

        history.append({"role": "user", "content": message})
        history.append(
            {"role": "assistant", "content": answer, "type": plan_type}
        )
        request.session["chat_history"] = history[-HISTORY_WINDOW:]
        request.session.modified = True

        return JsonResponse({"answer": answer})

    except Exception:
        # Log the real error server-side; never send exception internals
        # (stack traces, file paths, API error bodies) to the client.
        logger.exception("chat_api failed")
        return JsonResponse(
            {"error": "Something went wrong. Please try again."},
            status=500
        )