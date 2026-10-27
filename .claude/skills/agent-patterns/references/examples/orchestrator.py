"""Piece: orchestrator-workers. A model plans the tasks, Send starts one worker per task, a synthesizer joins them.

The worker is a subgraph with its own state (question, policy, context): it can be tested alone. Workers share
only `answers`, a list with the operator.add reducer. An empty plan goes straight to the synthesizer.
check_plan compares the plan with the policies a person expects: a badly split plan is this pattern's main risk.

Run from the repo root:
    uv run python .claude/skills/agent-patterns/references/examples/orchestrator.py
Cost: 1 (plan) + 1 per task (the plan decides how many, usually 3) + 1 (synthesis) model calls.
LangSmith: 1 trace only if LANGSMITH_TRACING=true.
"""

import operator
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from project import POLICY_FILES, build_model, policy_text
from pydantic import BaseModel, Field
from run_log import RunLog

Policy = Literal["credit", "disbursement", "fees", "collections"]

MESSAGE = (
    "Hola, soy C-3307 y tengo 75 días de mora. Quiero saber cuánto me pueden ampliar el plazo si reestructuro, "
    "si ya me reportaron a centrales de riesgo y si puedo pagar las cuotas por PSE desde otro banco."
)
# The policies a person expects for MESSAGE: restructuring and credit reports are collections; PSE is fees.
EXPECTED_POLICIES = {"collections", "fees"}


class Task(BaseModel):
    """One question of the ticket and the policy that answers it."""

    question: str = Field(description="One customer question, complete, in one sentence.")
    policy: Policy = Field(description="credit: requirements and amounts; disbursement; fees: costs and payments; "
                                       "collections: arrears, credit reports and restructuring.")


class Plan(BaseModel):
    """The distinct questions of a ticket."""

    tasks: list[Task] = Field(description="One task per distinct customer question.")


class TicketState(TypedDict, total=False):
    message: str
    tasks: list[dict]
    answers: Annotated[list[str], operator.add]
    reply: str


class WorkerState(TypedDict, total=False):
    question: str
    policy: str
    context: str
    answers: Annotated[list[str], operator.add]


def assign_workers(state: TicketState) -> list[Send] | str:
    """One worker per task, each with its own input. An empty plan skips the workers."""
    return [Send("worker", task) for task in state["tasks"]] or "synthesize"


def check_plan(tasks: list[dict], expected: set[str]) -> dict:
    """Deterministic check of the plan: which expected policies are missing, which are unexpected."""
    used = {task["policy"] for task in tasks}
    return {"missing": sorted(expected - used), "unexpected": sorted(used - expected)}


def build_worker(model):
    def load_policy(state: WorkerState) -> dict:
        return {"context": policy_text(POLICY_FILES[state["policy"]])}

    def answer(state: WorkerState) -> dict:
        messages = [
            SystemMessage("Answer in the customer's language, in one or two sentences, only with the policy, "
                          "citing each fact as [file, p. N]. If the policy does not answer it, say so."),
            HumanMessage(f"Policy:\n{state['context']}\n\nQuestion: {state['question']}"),
        ]
        return {"answers": [f"**{state['question']}** {model.invoke(messages).text}"]}

    builder = StateGraph(WorkerState)
    builder.add_sequence([load_policy, answer])
    builder.add_edge(START, "load_policy")
    return builder.compile()


def build_orchestrator(model):
    def orchestrator(state: TicketState) -> dict:
        plan = model.with_structured_output(Plan).invoke([HumanMessage(state["message"])])
        return {"tasks": [task.model_dump() for task in plan.tasks]}

    def synthesize(state: TicketState) -> dict:
        messages = [
            SystemMessage("You are the ACME support assistant. Join the answers into one message for the customer, "
                          "in their language, in at most six sentences. Keep the [file, p. N] citations. Add nothing new."),
            HumanMessage("\n\n".join(state.get("answers", [])) or f"No tasks. Customer message: {state['message']}"),
        ]
        return {"reply": model.invoke(messages).text}

    builder = StateGraph(TicketState)
    builder.add_node("orchestrator", orchestrator)
    builder.add_node("worker", build_worker(model))  # the subgraph, as one more node
    builder.add_node("synthesize", synthesize)
    builder.add_edge(START, "orchestrator")
    builder.add_conditional_edges("orchestrator", assign_workers, ["worker", "synthesize"])
    builder.add_edge("worker", "synthesize")
    builder.add_edge("synthesize", END)
    return builder.compile()


def main():
    support = build_orchestrator(build_model())
    run_log = RunLog()
    result = support.invoke({"message": MESSAGE}, config={"callbacks": [run_log]})
    print("Plan:")
    for task in result["tasks"]:
        print(f"  · [{task['policy']}] {task['question']}")
    print("Plan check:", check_plan(result["tasks"], EXPECTED_POLICIES))
    print("\nReply:\n", result["reply"])
    print(run_log.receipt())


if __name__ == "__main__":
    main()
