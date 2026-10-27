"""Project adapter: the only example file that knows this repository.

Every example and generated graph imports build_model and policy_text from here. To reuse the skill in
another project, rewrite this file (credentials, model, sample documents) and references/project.md.
"""

from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from langchain_anthropic import ChatAnthropic
from pypdf import PdfReader

MODEL = "claude-haiku-5-5"
ROOT = Path(__file__).resolve().parents[5]
# Synthetic ACME policies: two pages each, so a whole policy fits in one prompt.
POLICIES = ROOT / "datasets"
POLICY_FILES = {
    "credit": "acme_credit_policy.pdf",
    "disbursement": "acme_disbursement_policy.pdf",
    "fees": "acme_fees_guide.pdf",
    "collections": "acme_collections_policy.pdf",
}


def build_model(max_tokens: int = 500) -> ChatAnthropic:
    """Load the keys from the repository .env and create the default model."""
    load_dotenv(find_dotenv())  # never write a key in code
    return ChatAnthropic(
        model=MODEL,
        max_tokens=max_tokens,
        thinking={"type": "disabled"},  # without it, reasoning spends the token budget
        timeout=60,
        max_retries=2,
    )


def policy_text(name: str) -> str:
    """The whole text of one policy, each page labelled [file, p. N] so the model can cite it."""
    pages = PdfReader(POLICIES / name).pages
    return "\n\n".join(f"[{name}, p. {number}]\n{page.extract_text()}" for number, page in enumerate(pages, 1))
