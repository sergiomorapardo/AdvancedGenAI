# This project: AdvancedGenAI course repository

Everything that ties the skill to this repository lives here and in `examples/project.py`. To reuse the skill elsewhere, rewrite these two files; the rest of the skill stays as is.

## Model and credentials

- `examples/project.py` builds `ChatAnthropic(model="claude-haiku-5-5", thinking={"type": "disabled"}, timeout=60, max_retries=2)`; `build_model(max_tokens=...)` sets the budget (400 for chains and agents, 500 for RAG). No `temperature`: Haiku 5.5 rejects it. Do not switch to Sonnet or Opus on your own.
- Credentials: `load_dotenv(find_dotenv())` reads the repository `.env` (`ANTHROPIC_API_KEY`). Never write a key, never print `.env`.
- Embeddings: the open multilingual model `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` with `FastEmbedEmbeddings`, local. Anthropic has no embeddings; OpenAI is optional and stays commented in the notebooks.

## Where things live

- Generated apps: `labs/<app-name>/`, in a feature branch and its sibling worktree (`feature/<app-name>`), never on `main`; see `AGENTS.md`.
- Sample corpus of the examples: the synthetic ACME policies in `datasets/acme_*.pdf` (`SAMPLE_DOCUMENTS` in `project.py`). ACME is a fictional fintech; every figure is made up.
- Sample MCP servers of `mcp_agent.py`: the course servers `agents.servers.credits` (credit portfolio over SQLite, elicitation of the credit) and `agents.servers.documents` (policy search), started with `python -m` (`SAMPLE_MCP_SERVERS` in `project.py`), with Spanish data; `.mcp.json` registers them for Claude Code. To build or review a server, use the mcp-server skill.
- Install nothing outside uv. Everything the examples use is in `pyproject.toml`; if a package is really needed, propose `uv add` and wait.

## Budget and tracing

- LangSmith is off by default (`LANGSMITH_TRACING=false`) and the free tier has a monthly trace limit. Every top-level `invoke`, `batch` or `stream` is one trace, including `ChatPromptTemplate.invoke`.
- `langsmith` reads `LANGSMITH_TRACING` and `LANGSMITH_PROJECT` once: switch them with `tracing_context(enabled=True, project_name=...)`, not `os.environ`.

## Controls the repository enforces

- Hook `.claude/hooks/check_jinja.py`: after every edit of a `.jinja`, parses it and renders it with its `.example.json` under `StrictUndefined`.
- Hook `.claude/hooks/check_app.py`: after every edit of a Python file under `labs/`, checks syntax, `ruff`, no `temperature=` and no literal API key. If it fails, the message comes back to you: fix that and continue.
- Permissions in `.claude/settings.json` ask before running `labs/` and the skill examples: that is the "explicit yes" of a paid run, enforced by the harness.
- Offline tests of every example: `uv run python -m unittest tests.test_agentic_workflow`.

## The course behind each piece

The examples follow the course notebooks, which use the same ACME case and model.

| Piece | Week · notebook |
|---|---|
| `chain.py` | 1 · L1, L2 |
| `jinja_prompt.py` | 2 · L3 |
| `tools_agent.py`, `api_tool.py` | 3 · L4, L5 |
| `rag.py`, `vector_store.py` | 4 · L6, L7, L8 |
| `conversational_rag.py`, `memory_agent.py` | 5 · L9, L10 |
| Evaluation (evaluate-app skill) | 6 · L11 |
| `mcp_agent.py` (servers: mcp-server skill) | 7 · L12, L13 |
| LangGraph routing and parallel branches | 8 · L15, L16, L17, L18, L19 (not yet in the skill) |
| Human approval | 9 · L20 (not yet in the skill) |
| Orchestrator-workers and subgraphs | 10 · L21 (not yet in the skill) |
| Evaluator-optimizer | 11 · L22 (not yet in the skill) |
