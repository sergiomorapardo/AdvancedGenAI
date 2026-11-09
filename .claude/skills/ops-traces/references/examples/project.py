"""Project adapter: the only example file that knows this repository.

traces.py imports the credentials and the model price from here. To reuse the skill in another project,
rewrite this file and references/project.md.
"""

from dotenv import find_dotenv, load_dotenv

PRICE_PER_MILLION = {"input": 0.10, "output": 0.50}  # USD, claude-haiku-5-5; check the current price before reporting


def configure() -> None:
    """Load the repository .env (LANGSMITH_API_KEY included) without creating a model."""
    load_dotenv(find_dotenv())  # never print the key
