"""Piece: human approval before an action that cannot be undone, in a graph and in an agent.

1. A graph: validate → (up to 20 M) disburse, (20–40 M) approval, (over 40 M) reject. The approval node calls
   interrupt(): the graph stops, the checkpointer keeps its state under a thread_id, and Command(resume=...)
   continues with approve, reject or edit. The limits are code; no model is involved.
2. An agent: HumanInTheLoopMiddleware stops before the tool runs; the person approves, edits or rejects the call.

Run from the repo root:
    uv run python .claude/skills/agent-patterns/references/examples/approval.py
Cost: the graph makes no model calls; the agent about 4 (2 per request: propose the call, then answer).
LangSmith: 4 traces only if LANGSMITH_TRACING=true (pause and resume are separate invokes).
"""

from typing import Literal, TypedDict

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from project import build_model
from run_log import RunLog

AUTO_LIMIT = 20_000_000  # up to this amount, no person is needed
DAILY_LIMIT = 40_000_000  # above it, the policy forbids the disbursement


class Disbursement(TypedDict, total=False):
    customer: str
    amount_cop: int
    status: str
    reviewer_note: str


def validate(state: Disbursement) -> dict:
    return {"status": "validated"}


def route(state: Disbursement) -> Literal["disburse", "approval", "reject"]:
    if state["amount_cop"] > DAILY_LIMIT:
        return "reject"
    return "approval" if state["amount_cop"] > AUTO_LIMIT else "disburse"


def approval(state: Disbursement) -> Command[Literal["disburse", "reject"]]:
    # The graph stops here; the value goes to the application, which shows it to the person.
    decision = interrupt({
        "question": "Do you approve this disbursement?",
        "customer": state["customer"],
        "amount_cop": state["amount_cop"],
        "options": ["approve", "reject", "edit"],
    })
    if decision["type"] == "approve":
        return Command(goto="disburse")
    if decision["type"] == "edit":
        return Command(goto="disburse", update={"amount_cop": decision["amount_cop"]})
    return Command(goto="reject", update={"reviewer_note": decision.get("note", "rejected by the analyst")})


def disburse(state: Disbursement) -> dict:
    # Simulated: a real graph would call the payments platform here, once, after the approval.
    return {"status": f"disbursed {state['amount_cop']:,} COP to the ACME account of {state['customer']}"}


def reject(state: Disbursement) -> dict:
    return {"status": "rejected: " + state.get("reviewer_note", "over the daily limit of 40,000,000 COP")}


def build_graph(checkpointer=None):
    builder = StateGraph(Disbursement)
    for node in (validate, approval, disburse, reject):
        builder.add_node(node.__name__, node)
    builder.add_edge(START, "validate")
    builder.add_conditional_edges("validate", route)
    builder.add_edge("disburse", END)
    builder.add_edge("reject", END)
    # Without a checkpointer the graph can stop but never resume.
    return builder.compile(checkpointer=checkpointer or InMemorySaver())


@tool
def request_disbursement(customer: str, amount_cop: int) -> str:
    """Disburse an approved loan to the customer's ACME account. Moves money: requires approval."""
    return f"Disbursed {amount_cop:,} COP to the ACME account of {customer}."


def build_agent(model, checkpointer=None):
    return create_agent(
        model,
        tools=[request_disbursement],
        system_prompt="You are the ACME operations assistant. Answer in the user's language, in one or two sentences.",
        middleware=[HumanInTheLoopMiddleware(interrupt_on={"request_disbursement": True})],
        checkpointer=checkpointer or InMemorySaver(),
    )


def tool_executed(messages: list) -> bool:
    """Deterministic check: did the money-moving tool actually run?"""
    return any(message.type == "tool" and message.text.startswith("Disbursed") for message in messages)


def main():
    graph = build_graph()
    for thread, amount, answer in [
        ("d-001", 1_200_000, None),
        ("d-002", 25_000_000, {"type": "approve"}),
        ("d-003", 30_000_000, {"type": "reject", "note": "missing income statement"}),
        ("d-004", 28_000_000, {"type": "edit", "amount_cop": 20_000_000}),
    ]:
        config = {"configurable": {"thread_id": thread}}
        state = graph.invoke({"customer": "C-4415", "amount_cop": amount}, config)
        if "__interrupt__" in state:
            print(f"{thread} paused at {graph.get_state(config).next}: {state['__interrupt__'][0].value}")
            state = graph.invoke(Command(resume=answer), config)
        print(f"{thread} → {state['status']}")

    agent = build_agent(build_model(max_tokens=400))
    run_log = RunLog()
    for thread, request, decision in [
        ("agent-d-005", "Desembolsa 25.000.000 COP al cliente C-4415.", {"type": "approve"}),
        ("agent-d-006", "Desembolsa 35.000.000 COP al cliente C-3307.",
         {"type": "reject", "message": "The customer is 75 days past due; no disbursement."}),
    ]:
        config = {"configurable": {"thread_id": thread}, "callbacks": [run_log]}
        paused = agent.invoke({"messages": [HumanMessage(request)]}, config)
        [action] = paused["__interrupt__"][0].value["action_requests"]
        print(f"\n{thread} proposes {action['name']} {action['args']}")
        result = agent.invoke(Command(resume={"decisions": [decision]}), config)
        print(f"decision {decision['type']} · tool executed: {tool_executed(result['messages'])}")
        print(result["messages"][-1].text)
    print(run_log.receipt())


if __name__ == "__main__":
    main()
