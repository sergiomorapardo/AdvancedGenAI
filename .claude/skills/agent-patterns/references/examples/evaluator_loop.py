"""Piece: evaluator-optimizer. Generate, evaluate against a rubric, feed the feedback back, stop at a cap.

The loop always ends: approved, or MAX_ATTEMPTS reached. What code can check, code checks: the word limit is
counted in `evaluate` before trusting the judge, which in the course notebook approved a draft over the limit.

Run from the repo root:
    uv run python .claude/skills/agent-patterns/references/examples/evaluator_loop.py
Cost: 2 model calls per attempt (generate + evaluate), between 2 and 6 with MAX_ATTEMPTS = 3.
LangSmith: 1 trace only if LANGSMITH_TRACING=true.
"""

import operator
import re
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from project import POLICY_FILES, build_model, policy_text
from pydantic import BaseModel, Field
from run_log import RunLog

MAX_ATTEMPTS = 3
MAX_WORDS = 90
# Citations are required by the rubric: counting them as words would punish the answers that cite.
CITATION = re.compile(r"\[[^\]]+\.pdf, p\. \d+\]")
QUESTION = "Perdí mi empleo y no puedo pagar la cuota de mi crédito. ¿Qué opciones tengo?"

RUBRIC = f"""\
Approve only if the answer meets every point:
1. Figures and terms match the policy (grace period, termination letter, only once).
2. Every fact from the policy carries its [file, p. N] citation.
3. It promises no approvals and gives no personal financial advice.
4. It has at most {MAX_WORDS} words, not counting the citations.
"""


class Feedback(BaseModel):
    """Evaluation of an answer to an ACME customer."""

    grade: Literal["approved", "fix"] = Field(description="approved if it meets the whole rubric.")
    feedback: str = Field(description="What to fix, point by point; empty if approved.")


class DraftState(TypedDict, total=False):
    question: str
    draft: str
    feedback: str
    grade: str
    attempts: int
    history: Annotated[list[dict], operator.add]


def should_continue(state: DraftState) -> Literal["generate", "__end__"]:
    """The cap lives in code: without it, a strict evaluator could loop forever."""
    if state["grade"] == "approved" or state["attempts"] >= MAX_ATTEMPTS:
        return END
    return "generate"


def build_loop(model, policy: str = POLICY_FILES["collections"]):
    text = policy_text(policy)
    # The judge reasons before grading: more tokens and json_schema, so the format holds.
    judge = model.model_copy(update={"max_tokens": 1000}).with_structured_output(Feedback, method="json_schema")

    def generate(state: DraftState) -> dict:
        request = f"Policy:\n{text}\n\nCustomer question: {state['question']}"
        if state.get("feedback"):
            request += f"\n\nYour previous answer:\n{state['draft']}\n\nFix this:\n{state['feedback']}"
        # The generator knows the rules up front; without them, it learns the limit one attempt at a time.
        draft = model.invoke([
            SystemMessage("You are the ACME support assistant. Answer in the customer's language using only the "
                          f"policy, in at most {MAX_WORDS} words (citations do not count), and cite each fact as [file, p. N]. Write only the "
                          "answer for the customer, without mentioning the corrections."),
            HumanMessage(request),
        ]).text
        return {"draft": draft, "attempts": state.get("attempts", 0) + 1}

    def evaluate(state: DraftState) -> dict:
        words = len(CITATION.sub("", state["draft"]).split())
        if words > MAX_WORDS:  # a rule code can check never reaches the judge
            grade, feedback = "fix", f"It has {words} words; the limit is {MAX_WORDS}. Shorten it."
        else:
            result = judge.invoke([
                SystemMessage(f"You review ACME answers to customers.\n{RUBRIC}"),
                HumanMessage(f"Policy:\n{text}\n\nQuestion: {state['question']}\n\nAnswer:\n{state['draft']}"),
            ])
            grade, feedback = result.grade, result.feedback
        return {"grade": grade, "feedback": feedback,
                "history": [{"attempt": state["attempts"], "grade": grade, "words": words, "feedback": feedback}]}

    builder = StateGraph(DraftState)
    builder.add_node("generate", generate)
    builder.add_node("evaluate", evaluate)
    builder.add_edge(START, "generate")
    builder.add_edge("generate", "evaluate")
    builder.add_conditional_edges("evaluate", should_continue)
    return builder.compile()


def main():
    loop = build_loop(build_model())
    run_log = RunLog()
    result = loop.invoke({"question": QUESTION}, config={"callbacks": [run_log]})
    for step in result["history"]:
        print(f"Attempt {step['attempt']} · {step['grade']} · {step['words']} words")
        if step["feedback"]:
            print("   feedback:", step["feedback"][:300])
    print("\nFinal answer:\n", result["draft"])
    print(run_log.receipt())


if __name__ == "__main__":
    main()
