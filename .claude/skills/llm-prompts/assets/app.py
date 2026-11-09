"""TODO: one sentence with the goal of this app.

Run from the repo root:
    uv run python labs/TODO-app-name/app.py
Cost: 1 model call per run to the project model. LangSmith: 1 trace only if LANGSMITH_TRACING=true.

Delete the JINJA block if the prompt is inline. project.py and run_log.py are copied as is next to this file.
Evaluating the app is another skill.
"""

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from langchain_core.prompts import ChatPromptTemplate
from project import build_model
from pydantic import BaseModel, Field
from run_log import RunLog

# --- JINJA: versioned templates next to this file, strict about missing data -------------
TEMPLATES = Environment(
    loader=FileSystemLoader(Path(__file__).resolve().parent / "prompts"),
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)

MESSAGES = ChatPromptTemplate.from_messages([
    ("system", "{system_prompt}"),
    ("human", "{user_message}"),  # the user message is data, never rendered with Jinja
])


# --- OUTPUT: the fields that people or code will read ------------------------------------
class Result(BaseModel):
    """TODO: what this result describes."""

    answer: str = Field(description="TODO")
    issues: list[str] = Field(description="Missing or ambiguous data. Empty if none.")


def main():
    model = build_model()
    run_log = RunLog(Path(__file__).resolve().parent / "runs")

    # --- CHAIN: fixed steps --------------------------------------------------------------
    messages = MESSAGES.format_messages(
        system_prompt=TEMPLATES.get_template("TODO.jinja").render(today=datetime.now().astimezone().date().isoformat()),
        user_message="TODO",
    )
    result = model.with_structured_output(Result).invoke(messages, config={"callbacks": [run_log]})
    print(result.model_dump_json(indent=2))
    print(run_log.receipt())


if __name__ == "__main__":
    main()
