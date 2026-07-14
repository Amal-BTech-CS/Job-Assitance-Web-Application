from langgraph.graph import StateGraph, END

from accounts.ai.chatbot.langgraph_workflow.state import GraphState

from accounts.ai.chatbot.langgraph_workflow.nodes import (
    planner_node,
    execution_node,
    synthesizer_node,
)


builder = StateGraph(GraphState)

builder.add_node(
    "planner",
    planner_node
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

builder.add_edge(
    "planner",
    "executor"
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