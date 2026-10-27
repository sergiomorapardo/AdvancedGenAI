"""Piece: a fixed-step chain, chat template | model, with structured output.

Run from the repo root:
    uv run python .claude/skills/agentic-workflow/references/examples/chain.py
Cost: 1 model call to the project model. LangSmith: 1 trace only if LANGSMITH_TRACING=true.
"""

from langchain_core.prompts import ChatPromptTemplate
from project import build_model
from pydantic import BaseModel, Field
from run_log import RunLog

TICKET = (
    "Ticket T-2048: ACME customer C-1042 reports two identical charges of 185,000 COP on their "
    "debit card, made on October 12 at the same online store."
)

PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "Answer briefly, using only the context. "
        "If the data is missing, say it is not in the ticket. Never guess."
    )),
    ("human", "Context: {context}"),
    ("human", "Question: {question}"),
])


class Answer(BaseModel):
    """Short answer about the ticket and the data that supports it."""

    answer: str = Field(description="Answer to the question.")
    justification: str = Field(description="Exact data from the context that supports the answer.")


def build_chain(model):
    # Fixed steps: fill the template, call the model, validate the shape.
    return PROMPT | model.with_structured_output(Answer)


def main():
    chain = build_chain(build_model())
    run_log = RunLog()
    answer = chain.invoke(
        {"context": TICKET, "question": "How much is each charge?"},
        config={"callbacks": [run_log]},
    )
    print(answer.model_dump_json(indent=2))
    print(run_log.receipt())


if __name__ == "__main__":
    main()
