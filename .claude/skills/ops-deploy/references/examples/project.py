"""Project adapter: the only example file that knows this repository.

The example graph and API import build_model and database_uri from here. To reuse the skill in another
project, rewrite this file (credentials, model, database) and references/project.md.
"""

import os

from dotenv import find_dotenv, load_dotenv
from langchain_anthropic import ChatAnthropic

MODEL = "claude-haiku-5-5"

load_dotenv(find_dotenv())  # keys and DB_URI come from the repository .env; never write them in code


def build_model(max_tokens: int = 400) -> ChatAnthropic:
    """Create the default model."""
    return ChatAnthropic(
        model=MODEL,
        max_tokens=max_tokens,
        thinking={"type": "disabled"},  # without it, reasoning spends the token budget
        timeout=60,
        max_retries=2,
    )


def database_uri() -> str | None:
    """The PostgreSQL connection string for the checkpointer, or None to keep threads in memory."""
    return os.getenv("DB_URI")
