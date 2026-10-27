# Advanced Topics in Analytics II - Generative AI

> **Status: Course proposal · In development.** Proposed for Pontificia Universidad Javeriana. Approval, delivery dates, and teaching hours are pending confirmation.

*Instructor: Sergio A. Mora Pardo*

- email: <sergioa.mora@javeriana.edu.co>
- github: [sergiomorapardo](https://github.com/sergiomorapardo)


This proposed course builds on *Advanced Topics in Analytics*, moving from classic NLP and Graph Learning into the world of **Generative AI**. Students will learn how to build real applications powered by **Large Language Models (LLMs)**, covering prompt engineering, working with commercial LLM APIs (OpenAI, Anthropic/Claude), embeddings and vector databases, **Retrieval-Augmented Generation (RAG)** from basics to advanced techniques (re-ranking, hybrid search, query transformation), **AI agents** (ReAct, tool use, function calling), orchestration frameworks such as **LangChain** and **LangGraph**, the **Model Context Protocol (MCP)**, multi-agent systems, evaluation of LLM applications (LLM-as-judge with LangSmith and OpenEvals) and **LLMOps** for deployment. The course is project-oriented, with emphasis placed on writing software implementations that solve real-world problems end to end.

The examples share one running case: a fictional **fintech** whose assistant answers customers from its policies, looks up account data through tools and hands sensitive operations to a person. All data and documents are synthetic.


## Motivation

The original course (*Advanced Topics in Analytics*) taught students to **understand** language models — the NLP, embeddings and transformer foundations of how they work. This course takes the next step: it teaches students to **build** real systems that *use* those models, moving them from consumers of AI to engineers of AI.

Why this matters:

* **Employability** — RAG, LLM evaluation and LLMOps are precisely the skills companies are hiring GenAI and AI-application engineers for today.
* **Higher-order skills** — students progress from merely *applying* AI to *designing, evaluating and creating* AI systems.
* **Transferable, vendor-independent engineering** — the fundamentals of RAG, evaluation and agent architecture outlast any single model, provider or framework.

And one honest note: students will also learn **when *not* to reach for a heavy framework**. Recognizing that a direct API call is enough for the task at hand is itself a mark of good engineering judgment.


## Learning Outcomes

By the end of the course, students will be able to **design, connect (to real data), evaluate and deploy** LLM-powered applications.

| Module | Learning outcome |
| :----| :------------- |
| Intro to LLMs & LangChain | Call Anthropic and OpenAI models through LangChain; build message templates, structured outputs, and use `invoke`, `batch` and `stream`. |
| Prompt engineering & dynamic prompting | Craft structured prompts and render them from data with Jinja, validating inputs and outputs. |
| AI Agents fundamentals | Design agents that reason and use tools (ReAct, function calling) and check their answers against tool results. |
| Embeddings, Vector Databases & RAG | Represent text as embeddings, store/query them in FAISS and Chroma, and ground answers on documents with citations. |
| Conversational RAG & memory | Rewrite follow-up questions, use multi-query and hybrid search, measure retrieval, and keep per-thread memory. |
| Evaluation of LLM apps | Measure quality with datasets, code evaluators and calibrated LLM-as-judge (LangSmith, OpenEvals) instead of relying on vibe-checks. |
| MCP | Connect agents to external tools and data through the Model Context Protocol. |
| LangGraph | Build stateful, multi-step workflows with explicit control flow, routing and parallelization. |
| Human-in-the-loop | Pause a workflow for human approval and resume it with persistence. |
| Multi-agent systems | Orchestrate workers dynamically and delegate subtasks to subgraphs. |
| Evaluator-optimizer | Iterate on an answer with an evaluator until it meets explicit criteria. |
| LLMOps & Deployment | Deploy, monitor and manage the cost/latency of LLM apps in production. |


## Requirements

* [Python](https://www.python.org) 3.12 (pinned in [`.python-version`](./.python-version)) and [uv](https://docs.astral.sh/uv/), which installs the locked dependencies from [`pyproject.toml`](./pyproject.toml) and [`uv.lock`](./uv.lock);
* An [Anthropic](https://console.anthropic.com/) API key. Claude Haiku is the default model; OpenAI appears only as an optional alternative;
* A [LangSmith](https://smith.langchain.com/) API key for tracing and evaluation (free tier). Tracing stays off unless you enable it;
* [Docker](https://docs.docker.com/get-docker/), only for the PostgreSQL-backed examples.

Main libraries: [LangChain](https://docs.langchain.com/oss/python/langchain/overview), [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview), [LangSmith](https://docs.langchain.com/langsmith/home), [OpenEvals](https://github.com/langchain-ai/openevals), [Jinja](https://jinja.palletsprojects.com/), [FAISS](https://github.com/facebookresearch/faiss), [Chroma](https://www.trychroma.com/) and [Jupyter](https://jupyter.org/).

Follow [SETUP.md](./SETUP.md) to install the environment and configure your keys.

Git is out of the scope of this class, but please take a look at these [tutorials](https://docs.github.com/en/get-started/start-your-journey/git-and-github-learning-resources).

## Agent examples: single-file and modular

Both versions coexist intentionally for the course. Select `contact` or `support`
in LangGraph Studio to compare their organization:

| Graph | Entry point | Organization |
| :---- | :---- | :---- |
| `contact` | `src/agents/contact.py` | Original contact agent in one file, using the retrieval helpers from `rag.py`. |
| `support` | `src/agents/support/agent.py` | Modular contact agent with separate state, nodes, instructions, and tools. |

```text
src/agents/support/
├── agent.py                     # Graph construction and compilation
├── state.py                     # Shared conversation and contact state
└── nodes/
    ├── conversation/
    │   ├── node.py              # Model with document-search tools
    │   ├── prompt.py            # Conversation system prompt
    │   └── tools.py             # PDF retrieval and search_docs
    └── extractor/
        ├── node.py              # Contact schema and extraction
        └── prompt.py            # Extraction system prompt
```

The modular example keeps the same flow: extraction → conversation → optional
tools → conversation. It declares all extracted fields in its state and allows
missing contact values (`None`). Retrieval code is duplicated intentionally so
`support` does not import the single-file examples. Both use the same PDF and
Chroma locations (`data/pdfs` and `data/chroma`, configurable with `RAG_DATA_DIR`
and `RAG_CHROMA_DIR`). The `agent`, `simple`, and `rag` graphs remain available.

Each node returns a partial state update through `new_state`: LangGraph preserves
the other fields, and the `MessagesState` reducer integrates new messages into
the history. The extractor receives its system prompt together with the history
and uses the `ContactInfo` schema defined in its own `node.py`.

Within the same checkout, `rag`, `contact`, and `support` use the same Chroma
directory and collection (`advancedgenai-course-rag`). An existing nonempty
collection is reused without indexing the PDFs again. A separate worktree has
its own default `data/chroma` path; to reuse an existing database from another
checkout, set `RAG_CHROMA_DIR` to the absolute path of that existing directory.

Run the offline checks with `uv run python -m unittest discover -s tests -v`.
They simulate model responses and retrieval, including preservation of state
and reuse of a nonempty vector store, without making API calls.

From the checkout containing these files, configure `.env` as described above and
run `uv run langgraph dev`. The `support` graph is registered in `langgraph.json`.

## Local support chat API

The FastAPI demo runs the modular support graph with PostgreSQL checkpoints.
Use Python 3.12 or newer, Docker Compose, and the provider keys described above.
Set `DB_URI` in `.env` to the local connection string in `.env.example`, then run:

```sh
uv sync --locked --no-dev
docker compose up -d postgres
uv run --no-sync uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Wait for PostgreSQL to accept connections before starting the API. Startup creates
LangGraph's checkpoint tables; the database user needs schema creation privileges.
Open `http://127.0.0.1:8000/docs` for the endpoint schemas.

```sh
curl http://127.0.0.1:8000/chat/demo-thread \
  -H 'Content-Type: application/json' -d '{"message":"Hola"}'
curl -N http://127.0.0.1:8000/chat/demo-thread/stream \
  -H 'Content-Type: application/json' -d '{"message":"Recuerdas mi nombre?"}'
```

`POST /chat/{chat_id}` returns the saved message history after the new reply.
Reuse the same `chat_id` to continue a conversation, including after API restarts;
use another ID to start a separate history. The streaming endpoint emits SSE
`data:` events containing JSON objects with a `content` field (text or provider
content blocks). It hides extraction/routing output and closes the response when
the graph finishes. Calls execute in worker threads because this example uses the
synchronous graph and PostgreSQL saver. Send turns sequentially for each chat ID;
this demo does not serialize concurrent turns on the same conversation.

This is a local teaching demo with no authentication or chat ownership checks.
Keep the API on loopback; do not expose it publicly without access controls.
Compose binds PostgreSQL to loopback and uses demo-only credentials. API calls
use paid model services; document search also requires the configured PDF/vector
store. Studio keeps its existing `support:agent` entry point and manages its own
persistence independently.

`docker compose down` stops the database while preserving the `postgres_data`
volume. Removing that volume deletes saved conversations. For manual inspection,
replace the sample thread ID in [`docs/sql/checkpoints.sql`](docs/sql/checkpoints.sql).

## Claude Code: skills and hooks

Opening Claude Code in this repository loads three skills from [`.claude/skills/`](.claude/skills/), built on the same ACME case as the notebooks:

- [`/agentic-workflow`](.claude/skills/agentic-workflow/SKILL.md): designs and builds an LLM app step by step (chain, Jinja prompt, tools, RAG with citations, conversational memory, MCP tools) and runs it once only after approval.
- [`/evaluate-app`](.claude/skills/evaluate-app/SKILL.md): builds a LangSmith dataset, code evaluators and a calibrated judge, and compares two configurations of an existing app.
- [`/mcp-server`](.claude/skills/mcp-server/SKILL.md): builds an MCP server with the official SDK and reviews third-party servers before connecting them.

Hooks registered in [`.claude/settings.json`](.claude/settings.json) run after Claude edits a file, without calling a model: `check_jinja` renders `.jinja` templates with `StrictUndefined`, `check_app` lints apps under `labs/`, and `check_mcp` loads and reviews MCP servers. The same settings ask before running `labs/` or the skill examples, which spend tokens. [`.mcp.json`](.mcp.json) registers the course MCP servers. Run the offline tests of the skills with:

```sh
uv run --group quality python -m pytest -q tests/test_agentic_workflow.py tests/test_evaluate_app.py tests/test_mcp_server.py
```

## Continuous integration

GitHub Actions runs `.github/workflows/ci.yml` on pull requests and pushes to
`main`. A PR tests GitHub's temporary merge with its target branch; the `main`
run verifies the integrated commit. This avoids duplicate push/PR runs on feature
branches. New PR runs cancel older runs for that PR. The workflow also runs
weekly on Tuesday at 09:00 America/Bogota and supports manual dispatch.

The `unit-tests` job uses the Python version in `.python-version`, installs the
dependencies and quality tools from `uv.lock`, and runs the offline unit tests
under coverage.py. It fails if a test
fails, an import fails, or no tests are discovered. No model API keys, PDFs, or
running Chroma service are needed.

To run the tests locally:

```sh
uv sync --locked --no-dev
uv run --no-sync python -m unittest discover -s tests -v
```

The `langgraph-startup` job starts the real `langgraph dev` server, waits up to 90
seconds for readiness, and verifies that every graph in `langgraph.json` appears
in the assistants API. This catches missing exports, empty graph modules, and
import errors that mocked unit tests might miss. It uses placeholder credentials,
ignores local `.env` files, and stops the server after the check. It does not
invoke models or test PDF retrieval. Run it locally on macOS or Linux with:

```sh
uv sync --locked --dev
uv run --no-sync python .github/scripts/check_langgraph_startup.py
```

These checks validate the committed code in GitHub; they cannot detect empty or
unsaved files that exist only in a developer's local checkout.

The repository's `main protection` ruleset requires the `unit-tests` and
`langgraph-startup` checks from GitHub Actions before merging into `main`, with
the branch up to date. A missing, pending, or failed check blocks merging. This
server-side requirement is managed in GitHub's repository rules, separately from
the workflow file; keep the check names in sync if the jobs are renamed. Existing
pull-request and squash requirements remain in place, with no bypass actors.

### Unit test coverage in pull requests

The same `unit-tests` execution measures statements and branches across all
Python code under `src/`, including files not exercised by the tests. A separate
lightweight job named `coverage (XX.X%)` displays the total directly in the PR's
checks list, without rerunning tests or using an external reporting service.
The existing required `unit-tests` check keeps its name.

Open the coverage check for a per-file summary. Download the `coverage-report`
artifact from the workflow run and open `html/index.html` for uncovered lines
and branches. JSON, Markdown and HTML reports are retained for 1 day (24 hours). The
percentage combines statements and branches; tests, notebooks and CI scripts
are outside its scope. Coverage measures execution, not the quality of test
assertions. There is no minimum coverage threshold yet; test failures still
fail the required test job.

Run the tests with coverage locally:

```sh
uv sync --locked --no-dev --group quality
uv run --no-sync coverage run -m unittest discover -s tests -v
uv run --no-sync coverage report
uv run --no-sync coverage html
```

CI also rejects suites with no discovered tests. Generated reports are ignored
by Git; agents, notebooks and test implementations are not rewritten to collect
coverage.

### Quality checks and local hooks

The `quality` job installs tools from the separate `quality` dependency group,
runs read-only pre-commit hooks, scans Python with Bandit (medium/high severity),
and builds both a wheel and source distribution with `uv build`. The hooks check
fatal Python errors, JSON/notebook syntax, YAML, TOML, merge markers and private
keys. They do not rewrite files or execute notebooks. GitHub secret scanning and
push protection complement private-key detection for supported API credentials.

Install tools and run the same hooks locally:

```sh
uv sync --locked --only-group quality
uv run --no-sync pre-commit run --all-files
```

Once your checkout contains `.pre-commit-config.yaml`, opt in to running hooks
on each commit:

```sh
uv run --only-group quality pre-commit install
```

Installing hooks changes local Git configuration, outside the PR. Git worktrees
share the hooks directory, so install only after your active checkouts contain
the configuration. The PR adds the configuration without changing shared local
hooks automatically. CI runs the checks regardless of local hook installation.

Full Ruff lint (`E4,E7,E9,F,I`), format checking, mypy and `pip-audit` are
**temporarily advisory** while the existing findings are addressed in the cleaning
PR. Their exit statuses and dependency vulnerabilities appear in the Actions
summary; the `quality-reports` artifact retains detailed reports for 1 day (24 hours).
A successful `quality` job does not mean these advisory checks passed. Required
checks remain `unit-tests` and `langgraph-startup`; the new quality job is not
added to the GitHub ruleset by this PR.

Run the advisory code checks without applying fixes:

```sh
uv run --only-group quality pre-commit run ruff-full --all-files --hook-stage manual
uv run --only-group quality pre-commit run ruff-format --all-files --hook-stage manual
uv run --only-group quality pre-commit run mypy --hook-stage manual
```

Mypy initially ignores unavailable third-party stubs and skips imported-module
analysis; it still checks assignments and annotations in our source. Expand type
coverage after fixing the reported errors. Ruff starts with fatal checks only;
enable full lint and format gates after cleaning. No blanket vulnerability
exemptions are configured.

Dependabot proposes weekly updates for `uv.lock`/`pyproject.toml` and pinned
GitHub Actions, using Conventional Commit titles with Gitmoji. Security updates
are enabled separately in repository settings. PRs require review and checks;
updates are not merged automatically. See [dependency maintenance](docs/dependency-maintenance.md)
for the sunset review, security baseline and transition to blocking checks.

## Proposed Evaluation

* 50% Project
* 40% Exercises
* 10% Class participation

## Proposed Schedule

*Draft sequence of 12 weekly sessions. Calendar dates will be added once the course is approved and scheduled.*

### 1. Intro to LLMs & LangChain
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 1 | LangChain step by step: messages, templates, structured output and streaming | [L1 - LangChain step by step](./notebooks/L1-IntroToLLMs.ipynb) · [L11 - Structured output](./notebooks/L11-structured_output.ipynb) | |

### 2. Prompt engineering & dynamic prompting (Jinja)
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 2 | Dynamic prompts with Jinja, schemas and traces | [L12 - Dynamic prompting](./notebooks/L12-dynamic-prompting.ipynb) | |

### 3. AI Agents fundamentals (ReAct, tool use, function calling)
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 3 | Tools and a first agent, and tool calling with an external API | [L13 - Tools](./notebooks/L13-tools.ipynb) · [L19 - Tools with an external API](./notebooks/L19-ToolsAPI.ipynb) | |

### 4. Embeddings, Vector Databases & RAG (FAISS, Chroma)
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 4 | Embeddings, vector stores and answers with citations | [L3 - Embeddings](./notebooks/L3-Embeddings.ipynb) · [L2 - FAISS and Chroma](./notebooks/L2-PDFSearchFAISS.ipynb) · [L4 - RAG with citations](./notebooks/L4-RAG.ipynb) | |

### 5. Conversational RAG & memory (query transformation, hybrid search)
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 5 | Follow-up questions, multi-query, retrieval metrics and per-thread memory | [L18 - Conversational RAG](./notebooks/L18-ConversationalRAG.ipynb) · [L9 - Memory with an agent](./notebooks/L9-Memory.ipynb) | |

### 6. Evaluation of LLM apps (LLM-as-judge, OpenEvals)
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 6 | Evaluating LLM applications with LangSmith datasets, code evaluators and LLM-as-judge | [L5 - RAG evaluation](./notebooks/L5-RAGEvaluation.ipynb) | |

### 7. MCP - Model Context Protocol
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 7 | Connecting tools and data with the Model Context Protocol | [L20 - Building an MCP server](./notebooks/L20-MCPServer.ipynb) · [L21 - An agent with MCP tools](./notebooks/L21-MCPAgent.ipynb) | |

### 8. LangGraph (state, routing and parallelization)
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 8 | Stateful workflows with LangGraph: chaining, routing and parallelization | [L6 - LangGraph in Studio](./notebooks/L6-LangGraph.ipynb) · [L7 - Simple graph](./notebooks/L7-LangGraphSimple.ipynb) · [L8 - Messages](./notebooks/L8-LangGraphMessages.ipynb) · [L10 - Chaining](./notebooks/L10-chaining.ipynb) · [L14 - Routing](./notebooks/L14-Routing.ipynb) · [L15 - Parallelization](./notebooks/L15-Paralelization.ipynb) | |

### 9. Human-in-the-loop
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 9 | Persistence, approval and resumption | [L22 - Human-in-the-loop](./notebooks/L22-HumanInTheLoop.ipynb) | |

### 10. Multi-agent systems (orchestrator-workers)
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 10 | Dynamic delegation and subgraphs | [L16 - Orchestrator](./notebooks/L16-Orchestrator.ipynb) | |

### 11. Evaluator-optimizer
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 11 | Iterating an answer against an evaluator | [L17 - Evaluator-optimizer](./notebooks/L17-EvaluatorOptimizer.ipynb) | |

### 12. LLMOps & Deployment
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 12 | LLMOps: deploying and monitoring LLM applications |  | |

## Interest Links 🔗
Module | Topic | Material |
| :----| :----| :----|
| LangChain | Official Documentation | [LangChain Docs](https://python.langchain.com) |
| LangGraph | Official Documentation | [LangGraph Docs](https://langchain-ai.github.io/langgraph/) |
| MCP | Model Context Protocol | [modelcontextprotocol.io](https://modelcontextprotocol.io) |
| GenAI | Short Courses | [DeepLearning.AI Short Courses](https://www.deeplearning.ai/short-courses/) |

---

> 📚 This course is a proposed continuation ("part 2") of [Advanced Topics in Analytics](https://github.com/sergiomorapardo/AdvancedTopicsAnalytics), which covered MLOps, Deep Learning, NLP and Graph Learning.
