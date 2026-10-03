from pydantic import BaseModel, Field
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage

from agents.support.state import State
from agents.support.routes.intent.prompt import SYSTEM_PROMPT

class RouteIntent(BaseModel):
    """Contact information for a person."""

    step: Literal["conversation", "booking"] = Field(
        "conversation",  # default value
        description="The next step in the routin process"
    )

llm = init_chat_model(model="anthropic:claude-haiku-4-5", temperature=0, max_tokens=400)

llm = llm.with_structured_output(schema=RouteIntent)

def route_intent(state: State) -> Literal["conversation", "booking"]:
    history = state['messages']
    schema = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), *history])
    print(f"Routing intent: {schema.step}")
    if schema.step not in ["conversation", "booking"]:
        raise ValueError(f"Invalid step: {schema.step}")
    return schema.step
