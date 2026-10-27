"""Piece: prompt chaining in a StateGraph, with a gate in code between two steps.

classify → gate → extract → draft, or classify → gate → out_of_scope. The gate is a plain function:
it costs nothing and can be tested. Each step returns only the fields it changes.

Run from the repo root:
    uv run python .claude/skills/agent-patterns/references/examples/graph_chain.py
Cost: 4 model calls (3 for the credit message, 1 for the other one).
LangSmith: 2 traces only if LANGSMITH_TRACING=true, one per invoke.
"""

from typing import Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from project import POLICY_FILES, build_model, policy_text
from pydantic import BaseModel, Field
from run_log import RunLog


class Classification(BaseModel):
    """Topic of a customer message."""

    topic: Literal["credit", "other"] = Field(description="credit if it is about a loan, its arrears, disbursement or payments.")


class TicketData(BaseModel):
    """What the draft step needs to answer."""

    customer: str | None = Field(description="Customer code C-1234; None if the message has none.")
    question: str = Field(description="The customer's concrete question, in one sentence.")
    policy: Literal["credit", "disbursement", "fees", "collections"] = Field(
        description="The policy that answers it: credit, disbursement, fees and payments, or collections."
    )


class ChainState(TypedDict, total=False):
    message: str
    topic: str
    data: TicketData
    reply: str


OUT_OF_SCOPE = "This channel handles ACME loans. For other topics, write to general support."


def gate(state: ChainState) -> Literal["extract", "out_of_scope"]:
    """The control between steps: code, not a prompt."""
    return "extract" if state["topic"] == "credit" else "out_of_scope"


def build_chain(model):
    def classify(state: ChainState) -> dict:
        result = model.with_structured_output(Classification).invoke([HumanMessage(state["message"])])
        return {"topic": result.topic}

    def extract(state: ChainState) -> dict:
        return {"data": model.with_structured_output(TicketData).invoke([HumanMessage(state["message"])])}

    def draft(state: ChainState) -> dict:
        data = state["data"]
        messages = [
            SystemMessage(
                "You are the ACME support assistant. Answer in the customer's language, in at most four sentences, "
                "only with the policy you receive, and cite each fact as [file, p. N]. Never promise approvals."
            ),
            HumanMessage(f"Policy:\n{policy_text(POLICY_FILES[data.policy])}\n\n"
                         f"Customer: {data.customer}\nQuestion: {data.question}"),
        ]
        return {"reply": model.invoke(messages).text}

    def out_of_scope(state: ChainState) -> dict:
        return {"reply": OUT_OF_SCOPE}

    builder = StateGraph(ChainState)
    builder.add_node("classify", classify)
    builder.add_node("extract", extract)
    builder.add_node("draft", draft)
    builder.add_node("out_of_scope", out_of_scope)
    builder.add_edge(START, "classify")
    builder.add_conditional_edges("classify", gate)
    builder.add_edge("extract", "draft")
    builder.add_edge("draft", END)
    builder.add_edge("out_of_scope", END)
    return builder.compile()


def main():
    chain = build_chain(build_model())
    run_log = RunLog()
    for message in (
        "Soy C-3307, tengo 75 días de mora. ¿Me pueden reportar a centrales de riesgo?",
        "¿Ustedes venden seguros de carro?",
    ):
        print("=====", message)
        for step in chain.stream({"message": message}, config={"callbacks": [run_log]}, stream_mode="updates"):
            node, update = next(iter(step.items()))
            print(f"[{node}]", update.get("topic") or update.get("data") or update.get("reply"))
    print(run_log.receipt())


if __name__ == "__main__":
    main()
