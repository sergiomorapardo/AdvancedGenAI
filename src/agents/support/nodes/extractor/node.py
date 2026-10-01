from dotenv import find_dotenv, load_dotenv
from langchain.chat_models import init_chat_model

from agents.support.nodes.extractor.prompt import ContactInfo
from agents.support.state import State

load_dotenv(find_dotenv())

llm = init_chat_model("anthropic:claude-haiku-4-5", temperature=0)
llm_with_structured_output = llm.with_structured_output(schema=ContactInfo)


def extractor(state: State):
    history = state["messages"]
    customer_name = state.get("customer_name")
    if customer_name is None or len(history) >= 10:
        schema = llm_with_structured_output.invoke(history)
        return {
            "customer_name": schema.name,
            "name": schema.name,
            "email": schema.email,
            "phone": schema.phone,
            "age": schema.age,
        }
    return {}
