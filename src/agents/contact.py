import random

from dotenv import find_dotenv, load_dotenv
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from langgraph.graph import END, START, MessagesState, StateGraph

load_dotenv(find_dotenv())

llm = init_chat_model("openai:gpt-4o", temperature=1)
file_search_tool = {
    "type": "file_search",
    "vector_store_ids": ["vs_68cf0f0255e481919cd3be25b96c5080"],
}
llm = llm.bind_tools([file_search_tool])


class State(MessagesState):
    customer_name: str
    my_age: int


class ContactInfo(BaseModel):
    """Contact information for a person."""

    name: str = Field(description="The name of the person")
    email: str = Field(description="The email address of the person")
    phone: str = Field(description="The phone number of the person")
    tone: int = Field(description="The tone of the person", ge=0, le=100)
    age: int = Field(description="The age of the person")
    sentiment: str = Field(description="The sentiment conversation of the person")


llm_with_structured_output = init_chat_model(
    "anthropic:claude-3-5-sonnet-20240620",
    temperature=0,
)
llm_with_structured_output = llm.with_structured_output(schema=ContactInfo)


def extractor(state: State):
    last_message = state["messages"][-1]
    contact_info = llm_with_structured_output.invoke(last_message.text)
    return {
        "customer_name": contact_info.name,
        "my_age": contact_info.age,
    }


def conversation(state: State):
    new_state: State = {}
    if state.get("customer_name") is None:
        new_state["customer_name"] = "John Doe"
    else:
        new_state["my_age"] = random.randint(20, 30)

    history = state["messages"]
    last_message = history[-1]
    ai_message = llm.invoke(last_message.text)
    new_state["messages"] = [ai_message]
    return new_state


builder = StateGraph(State)
builder.add_node("conversation", conversation)
builder.add_node("extractor", extractor)

builder.add_edge(START, "extractor")
builder.add_edge("extractor", "conversation")
builder.add_edge("conversation", END)

agent = builder.compile()
