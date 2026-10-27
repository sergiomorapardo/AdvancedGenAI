"""The graph the API serves: a small tool agent, built by a factory that receives the checkpointer.

The API owns the checkpointer (one per process, opened in its lifespan) and passes it to make_graph on each
request. Any graph from the agentic-workflow or agent-patterns skills fits here if it exposes the same factory.
"""

from langchain.agents import create_agent
from langchain_core.tools import tool
from project import build_model

# Synthetic data of a fictional fintech.
OVERDUE = {"C-1042": 824_000, "C-3307": 2_070_000}

SYSTEM_PROMPT = (
    "You are the ACME support assistant. Answer in the customer's language, in at most two sentences. "
    "For overdue amounts always use the tool; if it does not find the customer, say so."
)


@tool(parse_docstring=True)
def lookup_overdue(customer: str) -> dict:
    """Look up the overdue amount of a customer, in Colombian pesos. Read only.

    Args:
        customer: customer code, for example C-1042.
    """
    if customer.upper() in OVERDUE:
        return {"status": "ok", "customer": customer.upper(), "overdue_cop": OVERDUE[customer.upper()]}
    return {"status": "not_found", "message": f"No customer {customer}."}


def make_graph(*, checkpointer=None, model=None):
    """One compiled agent per request; the state lives in the checkpointer, not in the object."""
    return create_agent(model or build_model(), tools=[lookup_overdue], system_prompt=SYSTEM_PROMPT,
                        checkpointer=checkpointer)
