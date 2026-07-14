from langgraph.graph import StateGraph, END

from accounts.ai.chatbot.langgraph_workflow.state import GraphState

from accounts.ai.chatbot.langgraph_workflow.nodes import (
    planner_node,
    route_after_planner,
    smalltalk_node,
    followup_node,
    condense_node,
    execution_node,
    synthesizer_node,
)


builder = StateGraph(GraphState)

builder.add_node(
    "planner",
    planner_node
)

builder.add_node(
    "smalltalk",
    smalltalk_node
)

builder.add_node(
    "followup",
    followup_node
)

builder.add_node(
    "condenser",
    condense_node
)

builder.add_node(
    "executor",
    execution_node
)

builder.add_node(
    "synthesizer",
    synthesizer_node
)

builder.set_entry_point(
    "planner"
)

# Planner classifies the question first, then routes to the cheapest
# path that can answer it: smalltalk (canned reply), followup (reformat
# the previous answer, no retrieval), or condenser -> executor (a real
# agent lookup that needs a standalone, retrieval-ready question).
builder.add_conditional_edges(
    "planner",
    route_after_planner,
    {
        "smalltalk": "smalltalk",
        "followup": "followup",
        "condenser": "condenser",
    },
)

builder.add_edge(
    "condenser",
    "executor"
)

builder.add_edge(
    "smalltalk",
    "synthesizer"
)

builder.add_edge(
    "followup",
    "synthesizer"
)

builder.add_edge(
    "executor",
    "synthesizer"
)

builder.add_edge(
    "synthesizer",
    END
)

graph = builder.compile()