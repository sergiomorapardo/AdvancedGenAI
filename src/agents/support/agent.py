from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agents.support.nodes import conversation, extractor, booking
from agents.support.routes.intent.route import route_intent
from agents.support.nodes.conversation.tools import search_docs
from agents.support.state import State


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

agent = builder.compile()
