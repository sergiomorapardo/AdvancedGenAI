from numpy import random

from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState, MessageGraph
from langchain.messages import AIMessage
from langchain.chat_models import init_chat_model

haiku_llm = init_chat_model("anthropic:claude-haiku-4-5", temperature=0)

class State(MessagesState):
    customer_name: str
    my_age: str

state: State = {}

def node_1(state: State):
    new_state: State = {}
    if state.get("customer_name") is None:
        new_state["customer_name"]= "John Doe"
    else:
        new_state["my_age"] = random.randint(20, 30)
    history = state["messages"]
    ai_message = haiku_llm.invoke(history)
    new_state["messages"] = [ai_message]
    return new_state

builder = StateGraph(State)
builder.add_node("node_1", node_1)

builder.add_edge(START, "node_1")
builder.add_edge("node_1", END)

agent = builder.compile()
