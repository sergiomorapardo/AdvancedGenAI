from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agents.support.nodes import conversation, extractor
from agents.support.nodes.conversation.tools import search_docs
from agents.support.state import State


builder = StateGraph(State)
builder.add_node("extractor", extractor)
builder.add_node("conversation", conversation)
builder.add_node("tools", ToolNode([search_docs]))

builder.add_edge(START, "extractor")
builder.add_edge("extractor", "conversation")
builder.add_conditional_edges("conversation", tools_condition)
builder.add_edge("tools", "conversation")

agent = builder.compile()
