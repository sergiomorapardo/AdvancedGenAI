from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agents.support.nodes import conversation, extractor, booking
from agents.support.routes.intent.route import route_intent
from agents.support.nodes.conversation.tools import search_docs
from agents.support.state import State


def make_graph(*, checkpointer: BaseCheckpointSaver | None = None):
    builder = StateGraph(State)
    builder.add_node("extractor", extractor)
    builder.add_node("conversation", conversation)
    builder.add_node("tools", ToolNode([search_docs]))
    builder.add_node("booking", booking)

    builder.add_edge(START, "extractor")
    builder.add_conditional_edges("extractor", route_intent)
    builder.add_conditional_edges("conversation", tools_condition)
    builder.add_edge("tools", "conversation")
    builder.add_edge("conversation", END)
    builder.add_edge("booking", END)

    return builder.compile(checkpointer=checkpointer)


# Studio supplies its own persistence; direct callers can inject a checkpointer.
agent = make_graph()
