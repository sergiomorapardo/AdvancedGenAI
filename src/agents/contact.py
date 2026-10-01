import random

from dotenv import find_dotenv, load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agents.rag import _format_documents, _get_retriever

load_dotenv(find_dotenv())

llm = init_chat_model("anthropic:claude-haiku-4-5", temperature=1)


@tool
def search_docs(query: str) -> str:
    """Busca información en los PDFs del curso. Úsala solo si la pregunta
    requiere consultar esos documentos."""
    return _format_documents(_get_retriever().invoke(query))


llm_with_tools = llm.bind_tools([search_docs])


class State(MessagesState):
    customer_name: str
    phone: str
    my_age: int


class ContactInfo(BaseModel):
    """Contact information for a person."""

    name: str = Field(description="The name of the person", default=None)
    email: str = Field(description="The email address of the person", default=None)
    phone: str = Field(description="The phone number of the person", default=None)
    age: int = Field(description="The age of the person", default=None)


llm_with_structured_output = init_chat_model("anthropic:claude-haiku-4-5", temperature=0)
llm_with_structured_output = llm_with_structured_output.with_structured_output(schema=ContactInfo)


def extractor(state: State):
    history = state["messages"]
    customer_name = state.get("customer_name", None)
    new_state: State ={}
    if customer_name is None or len(history) >= 10:
        schema = llm_with_structured_output.invoke(history)
        new_state['customer_name'] = schema.name
        new_state["name"] = schema.name
        new_state["email"] = schema.email
        new_state["phone"] = schema.phone
        new_state["age"] = schema.age
    return new_state


def conversation(state: State):
    new_state: State = {}
    history = state["messages"]
    customer_name = state.get("customer_name", "John Doe")
    system_message = SystemMessage(content=f"You are helpful assistant that can answer questions about the customer {customer_name}")
    ai_message = llm_with_tools.invoke([system_message, *history])
    new_state["messages"] = [ai_message]
    return new_state


builder = StateGraph(State)
builder.add_node("extractor", extractor)
builder.add_node("conversation", conversation)
builder.add_node("tools", ToolNode([search_docs]))

builder.add_edge(START, "extractor")
builder.add_edge("extractor", "conversation")
builder.add_conditional_edges("conversation", tools_condition)
builder.add_edge("tools", "conversation")

agent = builder.compile()
