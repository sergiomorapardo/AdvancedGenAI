# Advanced Topics in Analytics II - Generative AI

> **Status: Course proposal · In development.** Proposed for Pontificia Universidad Javeriana. Approval, delivery dates, and teaching hours are pending confirmation.

*Instructor: Sergio A. Mora Pardo* · <sergioa.mora@javeriana.edu.co> · [GitHub](https://github.com/sergiomorapardo)

This course continues [Advanced Topics in Analytics](https://github.com/sergiomorapardo/AdvancedTopicsAnalytics): students move from *understanding* language models to *building* applications with them. Over 12 weeks they design, connect, evaluate and deploy LLM applications with **LangChain**, **LangGraph**, **RAG**, the **Model Context Protocol (MCP)**, **LangSmith** and **OpenEvals**, and learn when a direct API call is enough.

Every example shares one case: **ACME**, a fictional fintech whose support assistant answers from its policies with citations, looks up the credit portfolio through tools and hands money movements to a person. All data and documents are synthetic.

## Learning outcomes

By the end of the course you will be able to:

- Connect language models to documents, data and tools, and answer with citations.
- Choose and build workflows with state, memory, specialists and human approval, and explain why a pattern fits better than a simpler one.
- Evaluate answers and agent behaviour with datasets, code evaluators and an LLM judge calibrated against human review, comparing quality, cost and latency.
- Deploy an assistant as an API with persistent memory, diagnose its failures and evaluate changes again before shipping them.

Three guides go with the schedule: [agentic patterns](docs/patterns.md) compares the workflow structures and when to use each, [readings](docs/readings.md) lists book chapters and code for every week, and the [demo guide](docs/demo.md) walks through the week 12 API.

## Schedule

*Draft sequence of 12 weekly sessions. Calendar dates will be added once the course is approved and scheduled.*

### 1. Foundations with LangChain · weeks 1–3

| Week | Session | Notebooks | Presentation |
| :-- | :-- | :-- | :-- |
| 1 | Messages, templates, structured output and streaming | [L01 · LangChain step by step](./notebooks/L01-IntroToLLMs.ipynb)<br>[L02 · Structured output](./notebooks/L02-StructuredOutput.ipynb) | [W01 · LangChain](./notebooks/W01-LangChain.pdf) |
| 2 | Dynamic prompts with Jinja, schemas and traces | [L03 · Dynamic prompting](./notebooks/L03-DynamicPrompting.ipynb) | [W02 · Jinja](./notebooks/W02-Jinja.pdf) |
| 3 | Tools, a first agent and an external API | [L04 · Tools](./notebooks/L04-Tools.ipynb)<br>[L05 · Tools with an external API](./notebooks/L05-ToolsAPI.ipynb) | [W03 · Tools](./notebooks/W03-Tools.pdf) |

### 2. RAG and evaluation · weeks 4–6

| Week | Session | Notebooks | Presentation |
| :-- | :-- | :-- | :-- |
| 4 | Embeddings, vector stores and answers with citations | [L06 · Embeddings](./notebooks/L06-Embeddings.ipynb)<br>[L07 · FAISS and Chroma](./notebooks/L07-VectorStores.ipynb)<br>[L08 · RAG with citations](./notebooks/L08-RAG.ipynb) | [W04 · RAG](./notebooks/W04-RAG.pdf) |
| 5 | Follow-up questions, multi-query, retrieval metrics and memory | [L09 · Conversational RAG](./notebooks/L09-ConversationalRAG.ipynb)<br>[L10 · Memory with an agent](./notebooks/L10-Memory.ipynb) | [W05 · Conversational RAG](./notebooks/W05-ConversationalRAG.pdf) |
| 6 | Datasets, code evaluators and a calibrated LLM-as-judge | [L11 · RAG evaluation](./notebooks/L11-RAGEvaluation.ipynb) | [W06 · Evaluation](./notebooks/W06-Evaluation.pdf) |

### 3. Model Context Protocol · week 7

| Week | Session | Notebooks | Presentation |
| :-- | :-- | :-- | :-- |
| 7 | Building MCP servers and an agent that uses them | [L12 · MCP server](./notebooks/L12-MCPServer.ipynb)<br>[L13 · Agent with MCP tools](./notebooks/L13-MCPAgent.ipynb) | [W07 · MCP](./notebooks/W07-MCP.pdf) |

### 4. LangGraph and agentic patterns · weeks 8–11

| Week | Session | Notebooks | Presentation |
| :-- | :-- | :-- | :-- |
| 8 | State, prompt chaining, routing and parallelization | [L14 · LangGraph in Studio](./notebooks/L14-LangGraphStudio.ipynb)<br>[L15 · Simple graph](./notebooks/L15-LangGraphSimple.ipynb)<br>[L16 · Messages](./notebooks/L16-LangGraphMessages.ipynb)<br>[L17 · Chaining](./notebooks/L17-Chaining.ipynb)<br>[L18 · Routing](./notebooks/L18-Routing.ipynb)<br>[L19 · Parallelization](./notebooks/L19-Parallelization.ipynb) | [W08 · LangGraph](./notebooks/W08-LangGraph.pdf) |
| 9 | Human-in-the-loop: persistence, approval and resumption | [L20 · Human-in-the-loop](./notebooks/L20-HumanInTheLoop.ipynb) | [W09 · Human-in-the-loop](./notebooks/W09-HumanInTheLoop.pdf) |
| 10 | Orchestrator-workers and subgraphs | [L21 · Orchestrator](./notebooks/L21-Orchestrator.ipynb) | [W10 · Orchestrator](./notebooks/W10-Orchestrator.pdf) |
| 11 | Evaluator-optimizer | [L22 · Evaluator-optimizer](./notebooks/L22-EvaluatorOptimizer.ipynb) | [W11 · Evaluator-optimizer](./notebooks/W11-EvaluatorOptimizer.pdf) |

### 5. LLMOps and deployment · week 12

| Week | Session | Notebooks | Presentation |
| :-- | :-- | :-- | :-- |
| 12 | The ACME assistant as an API with persistent memory | [Local support chat API](#local-support-chat-api) | [W12 · Deployment](./notebooks/W12-Deployment.pdf) |

**Proposed evaluation:** 50% project · 40% exercises · 10% class participation.

## Getting started

You need Python 3.12 with [uv](https://docs.astral.sh/uv/), an [Anthropic](https://console.anthropic.com/) API key (Claude Haiku is the default model), a [LangSmith](https://smith.langchain.com/) key for tracing and evaluation (tracing stays off unless you enable it) and [Docker](https://docs.docker.com/get-docker/) only for the PostgreSQL examples. Follow [SETUP.md](./SETUP.md) to install the environment and configure your keys.

The notebooks are versioned **executed**, so their outputs and diagrams can be read on GitHub before running anything. After editing one, refresh its Mermaid diagrams (no model calls) or rerun it against Claude Haiku with [`tests/run_notebooks.py`](./tests/run_notebooks.py):

```sh
uv run python tests/run_notebooks.py diagrams L08-RAG.ipynb
uv run python tests/run_notebooks.py execute L08-RAG.ipynb   # spends tokens
```

## Local support chat API

The FastAPI demo serves the ACME support agent ([`src/agents/acme.py`](src/agents/acme.py)) with PostgreSQL checkpoints. It joins cited search over the policies (week 4), the read-only credit portfolio of the MCP server (week 7) and memory per conversation (week 5). Set `DB_URI` in `.env` as in `.env.example`, then:

```sh
uv sync --locked --no-dev
docker compose up -d postgres
uv run --no-sync uvicorn api.main:app --host 127.0.0.1 --port 8000

curl http://127.0.0.1:8000/chat/demo-thread \
  -H 'Content-Type: application/json' -d '{"message":"Soy el cliente C-3307, ¿cuánto tengo vencido?"}'
curl -N http://127.0.0.1:8000/chat/demo-thread/stream \
  -H 'Content-Type: application/json' -d '{"message":"¿Y todavía puedo reestructurarlo?"}'
```

Reuse a `chat_id` to continue a conversation, even after restarting the API; the stream endpoint sends SSE `data:` events and hides tool output. The [demo guide](docs/demo.md) explains each turn, its model calls, a test script and how to diagnose errors. Endpoint schemas are at `http://127.0.0.1:8000/docs`, and [`docs/sql/checkpoints.sql`](docs/sql/checkpoints.sql) inspects the saved threads. This is a local teaching demo without authentication: keep it on loopback. Each turn calls a paid model, and the first policy search downloads the local embeddings model (~220 MB). `docker compose down` keeps the `postgres_data` volume.

## Repository

- **LangGraph Studio:** `uv run langgraph dev` opens the graphs in [`langgraph.json`](langgraph.json), including `acme` and the single-file (`contact`) and modular (`support`) versions of the same contact agent.
- **Claude Code:** nine skills in [`.claude/skills/`](.claude/skills/), named `<area>-<capability>` with five areas (`llm`, `agentic`, `mcp`, `eval`, `ops`), one responsibility each:

  | Skill | Builds or does | Weeks |
  | :-- | :-- | :-- |
  | [`/llm-prompts`](.claude/skills/llm-prompts/SKILL.md) | A fixed-step chain: chat or Jinja template, structured output | 1–2 |
  | [`/llm-tools`](.claude/skills/llm-tools/SKILL.md) | A tool agent: read-only tools, a public API, MCP tools with elicitation | 3, 7 |
  | [`/llm-rag`](.claude/skills/llm-rag/SKILL.md) | RAG with `[file, p. N]` citations, FAISS or Chroma, follow-up rewriting and multi-query | 4–5 |
  | [`/agentic-memory`](.claude/skills/agentic-memory/SKILL.md) | Memory per conversation and human approval before an action | 5, 9 |
  | [`/eval-experiments`](.claude/skills/eval-experiments/SKILL.md) | Datasets, code evaluators, a calibrated judge and experiments, including agents' tool calls and routes | 6, 11 |
  | [`/mcp-server`](.claude/skills/mcp-server/SKILL.md) | MCP servers, and a review of third-party ones | 7 |
  | [`/agentic-patterns`](.claude/skills/agentic-patterns/SKILL.md) | LangGraph workflows: chaining, routing, parallel branches, orchestrator-workers, evaluator-optimizer | 8–11 |
  | [`/ops-traces`](.claude/skills/ops-traces/SKILL.md) | Reads what a run left in LangSmith: traces, calls, latency, cost, branches, errors | 6–12 |
  | [`/ops-deploy`](.claude/skills/ops-deploy/SKILL.md) | Serves an app as an API with persistent threads and streaming | 12 |

  The W11 and W12 presentations use earlier names: `agent-patterns` is now `agentic-patterns`, and `deploy-app` is `ops-deploy`; `agentic-workflow` was split into the `llm-*` skills and `agentic-memory`, and `evaluate-app` is `eval-experiments`. Hooks in [`.claude/settings.json`](.claude/settings.json) check Jinja templates, apps and MCP servers without calling a model; [`.mcp.json`](.mcp.json) registers the course servers.
- **Guides:** [agentic patterns](docs/patterns.md), [readings by week](docs/readings.md) and the [API demo](docs/demo.md).
- **Tests and CI:** the tests run offline, simulating model responses. GitHub Actions requires `unit-tests` and `langgraph-startup` before merging into `main`; the `quality` job runs pre-commit hooks, Bandit and the package build, and reports coverage, Ruff, mypy and `pip-audit` as advisory. Dependabot proposes weekly updates; see [dependency maintenance](docs/dependency-maintenance.md).

```sh
uv sync --locked --dev --group quality
uv run --no-sync python -m pytest -q                              # offline tests
uv run --no-sync python .github/scripts/check_langgraph_startup.py
uv run --no-sync pre-commit run --all-files
```

## Interest links 🔗

[LangChain](https://docs.langchain.com/oss/python/langchain/overview) · [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) · [LangSmith](https://docs.langchain.com/langsmith/home) · [OpenEvals](https://github.com/langchain-ai/openevals) · [Model Context Protocol](https://modelcontextprotocol.io) · [Anthropic, Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) · [DeepLearning.AI short courses](https://www.deeplearning.ai/short-courses/)
