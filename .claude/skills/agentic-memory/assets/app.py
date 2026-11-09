"""TODO: one sentence with the goal of this app.

Run from the repo root:
    uv run python labs/TODO-app-name/app.py
Cost: about 2 model calls per turn that searches, 1 if the agent answers with what the thread already has;
state a range. LangSmith: 1 trace per turn only if LANGSMITH_TRACING=true.

project.py and run_log.py are copied as is next to this file. Evaluating the app is another skill.
"""

from pathlib import Path

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from project import build_model
from run_log import RunLog

# --- TOOLS: what the agent can look up. With documents, copy load_chunks, format_context and
# build_search_tool from references/examples/memory_agent.py; with tables, a read-only @tool.
TOOLS = []  # TODO

SYSTEM_PROMPT = (
    "TODO: role. Always look the data up with the tools before answering, and write each search as a "
    "complete question even when the user refers to earlier messages. Use only what the tools return."
)


def thread(thread_id: str) -> dict:
    # The thread_id comes from the user's session: two people must never share one.
    return {"configurable": {"thread_id": thread_id}}


def main():
    model = build_model(max_tokens=500)
    run_log = RunLog(Path(__file__).resolve().parent / "runs")
    # InMemorySaver lives in this process; a service needs a database checkpointer.
    agent = create_agent(model, tools=TOOLS, system_prompt=SYSTEM_PROMPT, checkpointer=InMemorySaver())
    conversation = thread("TODO")
    for question in ["TODO first question", "TODO follow-up"]:
        state = agent.invoke({"messages": [HumanMessage(question)]}, conversation | {"callbacks": [run_log]})
        print(state["messages"][-1].text)
    print(len(agent.get_state(conversation).values["messages"]), "messages in the thread")
    print(run_log.receipt())


if __name__ == "__main__":
    main()
