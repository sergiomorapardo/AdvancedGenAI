# Getting Started

This guide sets up the AdvancedGenAI course environment so you can run the notebooks and the LangGraph examples locally.

## Prerequisites

- **git**
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)**. It installs Python 3.12 (the version in `.python-version`) if you do not have it.
- An **Anthropic** API key. Claude Haiku is the default model in the notebooks.
- Optional: a **LangSmith** API key for tracing and evaluation, and an **OpenAI** key for the optional comparisons.
- Optional: **Docker**, only for the examples that store conversations in PostgreSQL.

## 1. Clone the repo

```bash
git clone https://github.com/sergiomorapardo/AdvancedGenAI.git
cd AdvancedGenAI
```

## 2. Install the locked dependencies

```bash
uv sync --locked
```

uv creates `.venv/` and installs exactly the versions in `uv.lock`. Do not install packages with `pip`; add new dependencies with `uv add <package>` (or `uv add --dev <package>`) so `pyproject.toml` and `uv.lock` change together.

## 3. Configure API keys

Copy the example environment file and add your keys:

```bash
cp .env.example .env
```

Then edit `.env`:

```
ANTHROPIC_API_KEY=your-anthropic-key-here
OPENAI_API_KEY=your-openai-key-here      # optional
LANGSMITH_API_KEY=your-langsmith-key-here # optional
LANGSMITH_TRACING=false
```

> **Note:** `.env` is gitignored and must **never** be committed — it holds your secret API keys.

Keep `LANGSMITH_TRACING=false` unless an exercise asks you to trace: every top-level `invoke`, `batch` or `stream` creates a trace, and the free tier has a monthly limit.

## 4. Launch Jupyter

```bash
uv run jupyter lab
```

Then open `notebooks/L01-IntroToLLMs.ipynb`. Select the kernel from `.venv` if Jupyter asks.

## 5. Run the graphs in LangGraph Studio

```bash
uv run langgraph dev
```

The graphs registered in `langgraph.json` appear in Studio. Every call to a graph uses your API key.

## Troubleshooting

- **Wrong Python version:** run `uv run python --version`; it should print 3.12.x. If not, run `uv python install` and `uv sync --locked` again.
- **Package not found:** run commands through `uv run` (or select the `.venv` kernel in Jupyter) so they use the project environment.
- **`uv sync --locked` fails:** the lock is out of date with `pyproject.toml`. Pull the latest `main`; do not edit `uv.lock` by hand.
- **API key not loaded:** check that `.env` exists in the repository root and contains the keys, then restart the Jupyter kernel.
