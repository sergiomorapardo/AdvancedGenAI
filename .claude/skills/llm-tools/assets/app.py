"""TODO: one sentence with the goal of this app.

Run from the repo root:
    uv run python labs/TODO-app-name/app.py
Cost: TODO model calls to the project model (an agent: 2 or more per question). LangSmith: TODO traces only if LANGSMITH_TRACING=true.

project.py and run_log.py are copied as is next to this file. Evaluating the app is another skill.
"""

import json
from pathlib import Path

from langchain.agents import create_agent
from langchain_core.tools import tool
from project import build_model
from run_log import RunLog

# --- TOOLS: read only, errors returned as data --------------------------------------------
DATA = [
    # TODO: 8-12 synthetic rows, with one or two traps (a zero balance, a missing customer).
]


@tool(parse_docstring=True)
def lookup_data(key: str) -> dict:
    """TODO: what it looks up. Read only.

    Args:
        key: TODO accepted values, listed explicitly.
    """
    for row in DATA:
        if row["key"].lower() == key.lower():
            return {"status": "ok", **row}
    return {"status": "not_found", "message": f"No record of '{key}'."}


# --- MCP: when several apps share the tools, load them from the servers instead: copy load_tools,
# server_config and build_agent from references/examples/mcp_agent.py.

SYSTEM_PROMPT = (
    "TODO: role. Always look up the data with the tools before answering. "
    "Use only the figures the tools return. If they do not find the data, say so."
)


def check_answer(messages: list) -> bool:
    """TODO: deterministic check that the answer uses the tool's data."""
    results = [json.loads(m.content) for m in messages if m.type == "tool"]
    return any(r["status"] == "ok" for r in results)


def main():
    model = build_model()
    run_log = RunLog(Path(__file__).resolve().parent / "runs")

    # --- AGENT: the model decides which tool to call -------------------------------------
    agent = create_agent(model, tools=[lookup_data], system_prompt=SYSTEM_PROMPT)
    state = agent.invoke(
        {"messages": [{"role": "user", "content": "TODO"}]},
        config={"callbacks": [run_log]},
    )
    print(state["messages"][-1].text)
    print("Answer matches the tool:", check_answer(state["messages"]))
    print(run_log.receipt())


if __name__ == "__main__":
    main()
