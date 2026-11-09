# This project: AdvancedGenAI course repository

Everything that ties the skill to this repository lives here and in `examples/project.py`. To reuse the skill elsewhere, rewrite these two files; the rest of the skill stays as is.

## Model and credentials

- `examples/project.py` builds `ChatAnthropic(model="claude-haiku-5-5", thinking={"type": "disabled"}, timeout=60, max_retries=2)`; `build_model(max_tokens=...)` sets the budget (500 for RAG). No `temperature`: Haiku 5.5 rejects it. Do not switch to Sonnet or Opus on your own.
- Credentials: `load_dotenv(find_dotenv())` reads the repository `.env` (`ANTHROPIC_API_KEY`). Never write a key, never print `.env`.
- Embeddings: the open multilingual model `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` with `FastEmbedEmbeddings`, local. Anthropic has no embeddings; OpenAI is optional and stays commented in the notebooks.

## Where things live

- Generated apps: `labs/<app-name>/`, in a feature branch and its sibling worktree (`feature/<app-name>`), never on `main`; see `AGENTS.md`.
- Sample corpus of the examples: the synthetic ACME policies in `datasets/acme_*.pdf` (`SAMPLE_DOCUMENTS` in `project.py`). ACME is a fictional fintech; every figure is made up.
- Install nothing outside uv. Everything the examples use is in `pyproject.toml`; if a package is really needed, propose `uv add` and wait.
- `examples/project.py` and `examples/run_log.py` are the same file in every skill that builds apps (`tests/test_skills.py` checks it): change them in all of them at once.

## Budget and tracing

- LangSmith is off by default (`LANGSMITH_TRACING=false`) and the free tier has a monthly trace limit. Every top-level `invoke`, `batch` or `stream` is one trace, including `ChatPromptTemplate.invoke`. Reading the traces a run left is the ops-traces skill.
- `langsmith` reads `LANGSMITH_TRACING` and `LANGSMITH_PROJECT` once: switch them with `tracing_context(enabled=True, project_name=...)`, not `os.environ`.

## Controls the repository enforces

- Hook `.claude/hooks/check_app.py`: after every edit of a Python file under `labs/`, checks syntax, `ruff`, no `temperature=` and no literal API key. If it fails, the message comes back to you: fix that and continue.
- Permissions in `.claude/settings.json` ask before running `labs/` and the skill examples: that is the "explicit yes" of a paid run, enforced by the harness.
- Offline tests of every example: `uv run python -m pytest tests/test_llm_rag.py tests/test_skills.py`.

## The course behind each piece

The examples follow the course notebooks, which use the same ACME case and model.

| Piece | Week · notebook | Skill |
|---|---|---|
| Chain, structured output (`chain.py`) | 1 · L01, L02 | llm-prompts |
| Jinja templates (`jinja_prompt.py`) | 2 · L03 | llm-prompts |
| Tools and an API tool (`tools_agent.py`, `api_tool.py`) | 3 · L04, L05 | llm-tools |
| RAG and persistent indexes (`rag.py`, `vector_store.py`) | 4 · L06, L07, L08 | llm-rag |
| Follow-up questions (`conversational_rag.py`) | 5 · L09 | llm-rag |
| Memory per conversation (`memory_agent.py`) | 5 · L10 | agentic-memory |
| Evaluation | 6 · L11 | eval-experiments |
| MCP tools in an agent (`mcp_agent.py`); servers | 7 · L12, L13 | llm-tools; mcp-server |
| Chaining, routing and parallel branches | 8 · L14–L19 | agentic-patterns |
| Human approval (`approval.py`) | 9 · L20 | agentic-memory |
| Orchestrator-workers and subgraphs | 10 · L21 | agentic-patterns |
| Evaluator-optimizer | 11 · L22 | agentic-patterns |
| Reading what a run left in LangSmith | 6–12 | ops-traces |
| Serving the app as an API | 12 · [demo](../../../../docs/demo.md) | ops-deploy |
