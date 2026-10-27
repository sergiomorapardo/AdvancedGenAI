"""Piece: parallelization. Three reviewers read the same draft at the same time; an aggregator in code decides.

Every reviewer writes to `reviews`, a list with the operator.add reducer: without it the three updates of the
same step collide (InvalidUpdateError). The aggregator is code: send only when no reviewer rejects.

Run from the repo root:
    uv run python .claude/skills/agent-patterns/references/examples/graph_parallel.py
Cost: 3 model calls, at the same time; the wall time is close to the slowest one.
LangSmith: 1 trace only if LANGSMITH_TRACING=true.
"""

import operator
import time
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from project import POLICY_FILES, build_model, policy_text
from pydantic import BaseModel, Field
from run_log import RunLog

QUESTION = "Perdí mi empleo y no puedo pagar la cuota. ¿Qué opciones tengo?"
# A bad draft on purpose: the policy grants up to 3 months, paying interest and insurance, with a letter within 30 days.
DRAFT = (
    "Tranquilo, te aprobamos un periodo de gracia de 6 meses en el que no pagas nada. "
    "Solo envíanos la carta de despido cuando puedas."
)

# One criterion per reviewer. Each prompt says to ignore the others, or the reviewers judge everything.
CRITERIA = {
    "compliance": "Reject if it promises approvals, terms or benefits, or gives personal financial advice.",
    "accuracy": "Reject if any figure, term or condition differs from the policy.",
    "tone": "Reject if it is not clear and respectful. Judge only the tone, not the content.",
}


class Review(BaseModel):
    """One reviewer's verdict on an answer to a customer."""

    approved: bool = Field(description="true if the answer meets the criterion.")
    issue: str = Field(description="The main problem in one sentence; empty if approved.")


class ReviewState(TypedDict, total=False):
    question: str
    draft: str
    reviews: Annotated[list[dict], operator.add]
    decision: str


def aggregate(state: ReviewState) -> dict:
    """Code decides: send only when every reviewer approves."""
    rejected = [review for review in state["reviews"] if not review["approved"]]
    return {"decision": "send" if not rejected else "fix: " + " | ".join(r["issue"] for r in rejected)}


def build_review(model, policy: str = POLICY_FILES["collections"]):
    def reviewer(name: str):
        def review(state: ReviewState) -> dict:
            messages = [
                SystemMessage(f"You review ACME answers to customers. Criterion: {CRITERIA[name]}"),
                HumanMessage(f"Policy:\n{policy_text(policy)}\n\n"
                             f"Customer question: {state['question']}\nProposed answer: {state['draft']}"),
            ]
            result = model.with_structured_output(Review).invoke(messages)
            return {"reviews": [{"criterion": name, **result.model_dump()}]}

        return review

    builder = StateGraph(ReviewState)
    for name in CRITERIA:
        builder.add_node(name, reviewer(name))
        builder.add_edge(START, name)  # fan-out: three branches from the same point
        builder.add_edge(name, "aggregate")  # fan-in: aggregate waits for the three
    builder.add_node("aggregate", aggregate)
    builder.add_edge("aggregate", END)
    return builder.compile()


def main():
    graph = build_review(build_model())
    run_log = RunLog()
    start = time.perf_counter()
    result = graph.invoke({"question": QUESTION, "draft": DRAFT}, config={"callbacks": [run_log]})
    for review in result["reviews"]:
        print(f"{review['criterion']:10} approved={review['approved']} · {review['issue']}")
    print("\nDecision:", result["decision"])
    print(f"Wall time: {time.perf_counter() - start:.1f} s")
    print(run_log.receipt())


if __name__ == "__main__":
    main()
