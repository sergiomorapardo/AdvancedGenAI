"""Piece: a versioned Jinja template, StrictUndefined and a structured review.

Run from the repo root:
    uv run python .claude/skills/agentic-workflow/references/examples/jinja_prompt.py
Cost: 1 model call to the project model. LangSmith: 1 trace only if LANGSMITH_TRACING=true
(format_messages fills the template without creating a trace).
"""

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from langchain_core.prompts import ChatPromptTemplate
from project import build_model
from pydantic import BaseModel, Field
from run_log import RunLog

# Resolve templates from this file, not from the working directory.
PROMPTS = Path(__file__).resolve().parent / "prompts"
# StrictUndefined: a missing variable raises an error instead of rendering an empty string.
TEMPLATES = Environment(
    loader=FileSystemLoader(PROMPTS), undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True
)

# The user message is data: it goes into the human message and is never rendered with Jinja.
MESSAGES = ChatPromptTemplate.from_messages([
    ("system", "{system_prompt}"),
    ("human", "{user_message}"),
])

TICKET = {
    "code": "T-2049",
    "customer": "C-1042",
    "product": "debit card",
    "charges": [  # not "items": in Jinja ticket.items resolves to dict.items
        {"amount": 185000, "currency": "COP", "merchant": "online store"},
        {"amount": 185000, "currency": "COP", "merchant": "online store"},
    ],
    "charge_date": "yesterday",
}
RULES = [
    "If the charge date is relative (for example, 'yesterday'), report it as missing.",
    "Do not convert amounts between currencies or round them.",
]


class TicketReview(BaseModel):
    """Review of a ticket before opening a charge dispute."""

    customer: str = Field(description="Code of the customer who reports the problem.")
    disputed_charges: int = Field(description="Number of charges the customer asks to review.")
    charge_date: str | None = Field(description="Exact charge date YYYY-MM-DD, or null if missing or relative.")
    issues: list[str] = Field(description="Missing or ambiguous data that blocks the dispute.")


def render_system_prompt(ticket: dict, rules: list[str]) -> str:
    return TEMPLATES.get_template("ticket.jinja").render(
        today=datetime.now().astimezone().date().isoformat(), ticket=ticket, rules=rules
    )


def main():
    review_model = build_model().with_structured_output(TicketReview)
    messages = MESSAGES.format_messages(
        system_prompt=render_system_prompt(TICKET, RULES),
        user_message="Review this ticket before we open the dispute.",
    )
    run_log = RunLog()
    review = review_model.invoke(messages, config={"callbacks": [run_log]})
    print(review.model_dump_json(indent=2))
    print(run_log.receipt())


if __name__ == "__main__":
    main()
