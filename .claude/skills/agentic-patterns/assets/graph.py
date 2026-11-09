"""TODO: one sentence with the problem this graph solves.

Pattern: TODO (chaining · routing · parallelization · approval · orchestrator-workers · evaluator-optimizer).
Run from the repo root:
    uv run python labs/TODO/graph.py
Cost: TODO model calls per path. LangSmith: TODO traces only if LANGSMITH_TRACING=true.
"""

import operator
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from project import build_model
from pydantic import BaseModel, Field
from run_log import RunLog

MAX_ATTEMPTS = 3  # TODO: keep only in a loop


class Decision(BaseModel):
    """TODO: what the model decides in structured form."""

    choice: Literal["TODO_a", "TODO_b"] = Field(description="TODO: one line per option.")


class State(TypedDict, total=False):
    request: str
    choice: str
    results: Annotated[list[str], operator.add]  # TODO: only for fields written in parallel
    reply: str


def route(state: State) -> Literal["TODO_a", "TODO_b"]:
    """A decision in code: TODO."""
    return state["choice"]


def build_graph(model):
    def decide(state: State) -> dict:
        decision = model.with_structured_output(Decision).invoke([HumanMessage(state["request"])])
        return {"choice": decision.choice}

    def step_a(state: State) -> dict:
        reply = model.invoke([SystemMessage("TODO: instructions"), HumanMessage(state["request"])]).text
        return {"reply": reply}

    def step_b(state: State) -> dict:
        return {"reply": "TODO: a fixed answer, without the model"}

    builder = StateGraph(State)
    builder.add_node("decide", decide)
    builder.add_node("TODO_a", step_a)
    builder.add_node("TODO_b", step_b)
    builder.add_edge(START, "decide")
    builder.add_conditional_edges("decide", route)
    builder.add_edge("TODO_a", END)
    builder.add_edge("TODO_b", END)
    return builder.compile()


def main():
    graph = build_graph(build_model())
    run_log = RunLog()
    for request in ["TODO: an input for each path"]:
        for step in graph.stream({"request": request}, config={"callbacks": [run_log]}, stream_mode="updates"):
            print(step)
    print(run_log.receipt())


if __name__ == "__main__":
    main()
