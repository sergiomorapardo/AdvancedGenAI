"""Piece: routing. A classifier with structured output picks one specialist; each has its own prompt and policy.

The route is a Literal, so the classifier cannot invent a fifth one. keyword_route is the rule it replaces:
fast and free, and wrong on "Me quedé sin plata", which never says "mora". check_routes compares the
chosen routes with the expected ones, the first thing to evaluate in a router.

Run from the repo root:
    uv run python .claude/skills/agent-patterns/references/examples/graph_router.py
Cost: 6 model calls (1 route + 1 answer for each of the 3 questions).
LangSmith: 3 traces only if LANGSMITH_TRACING=true, one per invoke.
"""

from typing import Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from project import POLICY_FILES, build_model, policy_text
from pydantic import BaseModel, Field
from run_log import RunLog

Route = Literal["credit", "disbursement", "fees", "collections"]

# Synthetic questions with the route a person expects; the first one breaks the keyword rule.
QUESTIONS = {
    "Me quedé sin plata para lo de este mes, ¿qué pasa si no pago?": "collections",
    "¿Puedo recibir el préstamo en mi cuenta de otro banco?": "disbursement",
    "¿Cuánto es lo máximo que me prestan en el Crédito Express?": "credit",
}


class RouteDecision(BaseModel):
    """Which specialist answers an ACME customer's question."""

    route: Route = Field(
        description="credit: requirements, amounts or products; disbursement: disbursements and accounts; "
        "fees: installments, costs, payments and prepayments; collections: arrears, credit reports, restructuring or unemployment."
    )


class RouteState(TypedDict, total=False):
    question: str
    route: Route
    reply: str


def keyword_route(question: str) -> Route:
    """The rule a router replaces: it only sees words."""
    text = question.lower()
    for words, route in [(("mora", "atrasad"), "collections"), (("desembols",), "disbursement"), (("pagar", "cuota"), "fees")]:
        if any(word in text for word in words):
            return route
    return "credit"


def check_routes(results: dict[str, str], expected: dict[str, str]) -> dict[str, bool]:
    """Deterministic check: was each question sent where a person expects?"""
    return {question: results.get(question) == route for question, route in expected.items()}


def build_router(model):
    def router(state: RouteState) -> dict:
        decision = model.with_structured_output(RouteDecision).invoke([HumanMessage(state["question"])])
        return {"route": decision.route}

    def specialist(route: str):
        def answer(state: RouteState) -> dict:
            messages = [
                SystemMessage(
                    f"You are the ACME specialist in {route}. Answer in the customer's language, in at most three "
                    "sentences, only with the policy you receive, citing each fact as [file, p. N]. "
                    "If the policy does not answer it, say so."
                ),
                HumanMessage(f"Policy:\n{policy_text(POLICY_FILES[route])}\n\nQuestion: {state['question']}"),
            ]
            return {"reply": model.invoke(messages).text}

        return answer

    builder = StateGraph(RouteState)
    builder.add_node("router", router)
    for route in POLICY_FILES:
        builder.add_node(route, specialist(route))
        builder.add_edge(route, END)
    builder.add_edge(START, "router")
    builder.add_conditional_edges("router", lambda state: state["route"])
    return builder.compile()


def main():
    support = build_router(build_model())
    run_log = RunLog()
    routes = {}
    for question in QUESTIONS:
        result = support.invoke({"question": question}, config={"callbacks": [run_log]})
        routes[question] = result["route"]
        print(f"[{result['route']}] (rule: {keyword_route(question)}) {question}\n{result['reply']}\n")
    print("Routes as expected:", check_routes(routes, QUESTIONS))
    print(run_log.receipt())


if __name__ == "__main__":
    main()
