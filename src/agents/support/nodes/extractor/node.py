from dotenv import find_dotenv, load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field

from agents.support.nodes.extractor.prompt import SYSTEM_PROMPT
from agents.support.state import State

load_dotenv(find_dotenv())


class ContactInfo(BaseModel):
    """Contact information for a person."""

    name: str | None = Field(description="The name of the person", default=None)
    email: str | None = Field(description="The email address of the person", default=None)
    phone: str | None = Field(description="The phone number of the person", default=None)
    age: int | None = Field(description="The age of the person", default=None)


llm = init_chat_model("anthropic:claude-haiku-4-5", temperature=0)
llm_with_structured_output = llm.with_structured_output(schema=ContactInfo)


def extractor(state: State) -> State:
    history = state["messages"]
    customer_name = state.get("customer_name")
    # Actualización parcial: LangGraph conserva los campos que no devolvemos.
    new_state: State = {}
    if customer_name is None or len(history) >= 10:
        system_message = SystemMessage(content=SYSTEM_PROMPT)
        schema = llm_with_structured_output.invoke([system_message, *history])
        new_state["customer_name"] = schema.name
        new_state["name"] = schema.name
        new_state["email"] = schema.email
        new_state["phone"] = schema.phone
        new_state["age"] = schema.age
    return new_state
