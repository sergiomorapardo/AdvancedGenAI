"""Piece: a read-only @tool, errors as data, create_agent and an answer check.

Run from the repo root:
    uv run python .claude/skills/agentic-workflow/references/examples/tools_agent.py
Cost: 2 or more model calls to the project model (the agent loops until it answers).
LangSmith: 1 trace only if LANGSMITH_TRACING=true; it groups every model and tool call.
"""

import json
import re

from langchain.agents import create_agent
from langchain_core.tools import tool
from project import build_model
from run_log import RunLog

# Synthetic data of a fictional fintech: two traps, one customer up to date and one with 75 days past due.
CREDITS = [
    {"customer": "C-1042", "code": "CLI", "product": "crédito libre inversión", "installment": 412_000,
     "overdue_installments": 2, "days_past_due": 45},
    {"customer": "C-2210", "code": "CEX", "product": "crédito express", "installment": 215_000,
     "overdue_installments": 0, "days_past_due": 0},
    {"customer": "C-3307", "code": "CLI", "product": "crédito libre inversión", "installment": 690_000,
     "overdue_installments": 3, "days_past_due": 75},
]

SYSTEM_PROMPT = (
    "You are the support assistant of ACME, a fintech. "
    "To answer about overdue amounts, always check the credits with the tools. "
    "Use only the figures the tools return. If they do not find the data, say so."
)


@tool(parse_docstring=True)
def lookup_credit(customer: str, product: str, payment: int | None = None) -> dict:
    """Look up the overdue amount of a customer's credit, in Colombian pesos. Read only.

    Args:
        customer: customer code, for example C-1042.
        product: code (CLI, CEX) or product words (libre inversión, express).
        payment: payment in pesos the customer wants to make; when given, it is compared with the overdue amount.
    """
    for row in CREDITS:
        same_product = product.lower() in row["product"] or product.upper() == row["code"]
        if same_product and customer.upper() == row["customer"]:
            overdue = row["installment"] * row["overdue_installments"]
            result = {"status": "ok", "customer": row["customer"], "code": row["code"],
                      "overdue_cop": overdue, "days_past_due": row["days_past_due"]}
            if payment is not None:
                result["covers_overdue"] = payment >= overdue
                result["missing_cop"] = max(0, overdue - payment)
            return result
    # Return the problem as data: an exception would stop the agent without an answer.
    return {"status": "not_found", "message": f"No credit '{product}' for customer {customer}."}


def check_answer(messages: list) -> bool:
    """Deterministic check: the figure in the final answer must come from the tool.

    Compares digits only: the model may write 824.000, $824,000 or 824000."""
    results = [json.loads(m.content) for m in messages if m.type == "tool"]
    found = [r for r in results if r["status"] == "ok"]
    digits = re.sub(r"\D", "", messages[-1].text)
    return bool(found) and str(found[-1]["overdue_cop"]) in digits


def main():
    agent = create_agent(build_model(), tools=[lookup_credit], system_prompt=SYSTEM_PROMPT)
    run_log = RunLog()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "I am customer C-1042. How much is overdue on my Crédito Libre Inversión?"}]},
        config={"callbacks": [run_log]},
    )
    print(result["messages"][-1].text)
    print("Answer matches the tool:", check_answer(result["messages"]))
    print(run_log.receipt())


if __name__ == "__main__":
    main()
