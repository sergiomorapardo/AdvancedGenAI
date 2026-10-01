from dotenv import find_dotenv, load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage

from agents.support.nodes.conversation.prompt import SYSTEM_PROMPT
from agents.support.nodes.conversation.tools import search_docs
from agents.support.state import State

load_dotenv(find_dotenv())

llm = init_chat_model("anthropic:claude-haiku-4-5", temperature=1)
llm_with_tools = llm.bind_tools([search_docs])


def conversation(state: State):
    history = state["messages"]
    customer_name = state.get("customer_name", "John Doe")
    system_message = SystemMessage(
        content=SYSTEM_PROMPT.format(customer_name=customer_name)
    )
    ai_message = llm_with_tools.invoke([system_message, *history])
    return {"messages": [ai_message]}
