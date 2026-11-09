"""Project adapter: the only example file that knows this repository.

Every example and generated app imports build_model from here. To reuse the skill in another
project, rewrite this file (credentials, model, sample corpus) and references/project.md.
"""

import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from langchain_anthropic import ChatAnthropic

MODEL = "claude-haiku-5-5"
ROOT = Path(__file__).resolve().parents[5]
# Synthetic ACME policy PDFs that the RAG examples index. A generated app uses its own documents/ folder.
SAMPLE_DOCUMENTS = ROOT / "datasets"
# MCP servers that mcp_agent.py connects to: the course servers, started as modules.
SAMPLE_MCP_SERVERS = {
    "credits": [sys.executable, "-m", "agents.servers.credits"],
    "documents": [sys.executable, "-m", "agents.servers.documents"],
}


def build_model(max_tokens: int = 400) -> ChatAnthropic:
    """Load the keys from the repository .env and create the default model."""
    load_dotenv(find_dotenv())  # never write a key in code
    return ChatAnthropic(
        model=MODEL,
        max_tokens=max_tokens,
        thinking={"type": "disabled"},  # without it, reasoning spends the token budget
        timeout=60,
        max_retries=2,
    )
