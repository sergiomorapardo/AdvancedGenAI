# This project: AdvancedGenAI course repository

Everything that ties the skill to this repository lives here and in `examples/project.py`. To reuse the skill elsewhere, rewrite these two files; the rest of the skill stays as is.

## SDK and dependencies

- `pyproject.toml` pins the official SDK `mcp>=2.3,<3` and `langchain[mcp]` (`langchain.mcp`, for agents). Install nothing outside uv; if a server really needs a package, propose `uv add` and wait.
- Document search uses the open model `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` with `FastEmbedEmbeddings`, local. Anthropic has no embeddings; OpenAI is optional.
- The MCP Inspector needs Node 22.19 or newer, which is not part of the uv environment. `inspect_server.py` covers the review without Node.

## Where things live

- New servers: `labs/<server-name>/server.py`, in a feature branch and its sibling worktree (`feature/<server-name>`), never on `main`; see `AGENTS.md`.
- The course servers: `src/agents/servers/credits.py` (the ACME credit portfolio over SQLite, elicitation of the credit) and `src/agents/servers/documents.py` (search over the ACME policies), started with `python -m agents.servers.credits` and `python -m agents.servers.documents`. They are the Spanish versions of the two examples; read them with `notebooks/L20-MCPServer.ipynb` and `notebooks/L21-MCPAgent.ipynb` when the person comes from the course.
- Sample corpus: the synthetic ACME policies in `datasets/acme_*.pdf` (`SAMPLE_DOCUMENTS` in `project.py`). Synthetic credits: the seed of `credits_server.py`, the same figures as `datasets/acme_credits.sql`.
- `.mcp.json` at the repo root registers the course servers for Claude Code (`acme-creditos`, `acme-documentos`). Add a team server there only when the person chose project registration; it is shared with everyone who opens the repo.

## Controls the repository enforces

- Hook `.claude/hooks/check_mcp.py`: after every edit of a Python file that creates `<name> = MCPServer(...)`, rejects `print()`, loads the server, lists its tools in memory and applies `review_tools` from `examples/inspect_server.py`. If it fails, the message comes back to you: fix that and continue.
- Hook `.claude/hooks/check_app.py`: under `labs/`, also checks syntax, `ruff` and literal keys.
- Permissions in `.claude/settings.json` ask before running anything under `labs/` or the skill examples.
- Offline tests of the examples and the hook: `uv run python -m unittest tests.test_mcp_server`.

## Budget

The servers and every check of this skill make no model calls and create no LangSmith traces. An agent that uses the servers does: that run belongs to agentic-workflow and needs its own approval.

## The course behind each piece

Week 7 (`L20`, `L21`) builds the course servers and checks them with the SDK client in memory and over stdio, and with an agent on `claude-haiku-5-5` over stdio and HTTP. `tests/test_servers.py` covers both course servers offline.
