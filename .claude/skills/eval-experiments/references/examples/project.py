"""Project adapter: the only example file that knows this repository.

evaluation.py imports the model, the sample corpus and the sample evaluation set from here.
To reuse the skill in another project, rewrite this file and references/project.md.
"""

from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from langchain_anthropic import ChatAnthropic

MODEL = "claude-haiku-5-5"
PRICE_PER_MILLION = {"input": 0.10, "output": 0.50}  # USD; check the current price before reporting
ROOT = Path(__file__).resolve().parents[5]
SAMPLE_DOCUMENTS = ROOT / "datasets"  # the synthetic ACME policy PDFs
SAMPLE_QUESTIONS = ROOT / "datasets/acme_questions.csv"  # id, question, source, page, reference
SAMPLE_REVIEW_SET = ROOT / "datasets/acme_review_set.csv"  # review_id, id, answer, human_correct, note


def configure() -> None:
    """Load the repository .env (LANGSMITH_API_KEY included) without creating a model."""
    load_dotenv(find_dotenv())


def build_model(max_tokens: int = 500) -> ChatAnthropic:
    """Load the keys from the repository .env and create the default model."""
    configure()  # never write a key in code
    return ChatAnthropic(
        model=MODEL,
        max_tokens=max_tokens,
        thinking={"type": "disabled"},  # without it, reasoning spends the token budget
        timeout=60,
        max_retries=2,
    )
