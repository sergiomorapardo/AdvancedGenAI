"""Piece: an agent whose tools come from MCP servers, including a server that asks the person.

MCPAdapter reads the same "mcpServers" configuration as Claude Code and turns every MCP tool into a
LangChain tool named <server>_<tool>. The implementation stays in the servers: the agent only sees
names, descriptions and schemas. When a server asks the person (elicitation), the agent pauses with an
interrupt and resumes with Command(resume=...), which needs a checkpointer and a thread_id.

Run from the repo root; it asks you which product you meant:
    uv run python .claude/skills/agentic-workflow/references/examples/mcp_agent.py
Cost: about 4 model calls to the project model (2 or 3 for the first question, 1 or 2 after your
answer); state a range, the agent decides. The servers make no model calls; embeddings run locally.
LangSmith: 3 traces only if LANGSMITH_TRACING=true (the pause and the resume are two).
"""

import asyncio
import logging

from langchain.agents import create_agent
from langchain.mcp import MCPAdapter
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from project import SAMPLE_MCP_SERVERS, build_model
from run_log import RunLog

logging.getLogger("fastmcp").setLevel(logging.WARNING)  # one INFO line per tool call otherwise

SYSTEM_PROMPT = (
    "You are the support assistant of ACME, a fintech. Answer in the language of the question. "
    "For balances, overdue amounts and days past due, always check the credits tool and give the "
    "product and the figure in pesos. For requirements, deadlines or policies, search the documents "
    "with a complete question and cite each fact as [file, p. N]. Do not promise approvals. "
    "If the tools do not return the data, say so and do not invent it."
)

# The sample servers hold Spanish data, so the questions are in Spanish.
QUESTION = (
    "Soy el cliente C-3307. ¿Cuánto tengo vencido en mi Crédito Libre Inversión? "
    "¿Y con cuántos días de mora todavía puedo pedir una reestructuración?"
)
AMBIGUOUS = "Soy el cliente C-1042. ¿Cuánto tengo vencido?"  # the customer has two credits


def server_config(servers: dict) -> dict:
    """The mcpServers shape of .mcp.json. stdio starts each server with its command;
    a server already running over HTTP is {"url": "http://127.0.0.1:8002/mcp"}."""
    return {"mcpServers": {name: {"command": command, "args": args} for name, (command, *args) in servers.items()}}


async def load_tools(config: dict) -> list:
    """Ask every server what it offers. Each tool opens its own session when called, so the list
    keeps working after this block closes."""
    async with MCPAdapter(config) as adapter:
        return await adapter.list_tools()


def build_agent(model, tools, checkpointer=None):
    """Without a checkpointer the agent cannot pause for an elicitation and resume."""
    return create_agent(model, tools=tools, system_prompt=SYSTEM_PROMPT, checkpointer=checkpointer)


def tools_used(messages: list) -> list[str]:
    """The prefix of each tool name says which server answered."""
    return [call["name"] for m in messages if m.type == "ai" for call in m.tool_calls]


def pending_question(state: dict) -> dict | None:
    """The question a server is waiting for (key, message, requested_schema), or None if the agent finished."""
    interrupts = state.get("__interrupt__") or []
    return interrupts[0].value["requests"][0] if interrupts else None


def answer_from_person(request: dict) -> dict:
    """The person answers, never the model: accept with the data, or decline."""
    print(request["message"])
    content = {}
    for field, schema in request["requested_schema"]["properties"].items():
        options = schema.get("enum", [])
        choice = input(f"{field} {options} (empty to decline): ").strip()
        if not choice or (options and choice not in options):
            return {"action": "decline"}
        content[field] = choice
    return {"action": "accept", "content": content}


async def main():
    tools = await load_tools(server_config(SAMPLE_MCP_SERVERS))
    print("Tools:", [t.name for t in tools])
    agent = build_agent(build_model(max_tokens=500), tools, checkpointer=InMemorySaver())
    run_log = RunLog()

    config = {"configurable": {"thread_id": "two-servers"}, "callbacks": [run_log]}
    state = await agent.ainvoke({"messages": [HumanMessage(QUESTION)]}, config)
    print(state["messages"][-1].text)
    print("Tools used:", tools_used(state["messages"]))

    config = {"configurable": {"thread_id": "ambiguous-credit"}, "callbacks": [run_log]}
    state = await agent.ainvoke({"messages": [HumanMessage(AMBIGUOUS)]}, config)
    while request := pending_question(state):  # paused in the tool call until the person answers
        resume = {"responses": {request["key"]: answer_from_person(request)}}
        state = await agent.ainvoke(Command(resume=resume), config)
    print(state["messages"][-1].text)
    print("Tools used:", tools_used(state["messages"]))
    print(run_log.receipt())


if __name__ == "__main__":
    asyncio.run(main())
