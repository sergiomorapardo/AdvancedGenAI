# Advanced Topics in Analytics II - Generative AI

> **Status: Course proposal · In development.** Proposed for Pontificia Universidad Javeriana. Approval, delivery dates, and teaching hours are pending confirmation.

*Instructor: Sergio A. Mora Pardo*

- email: <sergioa.mora@javeriana.edu.co>
- github: [sergiomorapardo](https://github.com/sergiomorapardo)


This proposed course builds on *Advanced Topics in Analytics*, moving from classic NLP and Graph Learning into the world of **Generative AI**. Students will learn how to build real applications powered by **Large Language Models (LLMs)**, covering prompt engineering, working with commercial LLM APIs (OpenAI, Anthropic/Claude), embeddings and vector databases, **Retrieval-Augmented Generation (RAG)** from basics to advanced techniques (re-ranking, hybrid search, query transformation), **AI agents** (ReAct, tool use, function calling), orchestration frameworks such as **LangChain** and **LangGraph**, the **Model Context Protocol (MCP)**, multi-agent systems, evaluation of LLM applications (LLM-as-judge, RAGAS) and **LLMOps** for deployment. The course is project-oriented, with emphasis placed on writing software implementations that solve real-world problems end to end.


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
| Intro to LLMs & Prompt Engineering | Explain how LLMs work and craft effective, structured prompts. |
| Working with LLM APIs | Integrate OpenAI and Anthropic APIs; manage tokens, parameters and streaming. |
| Embeddings & Vector Databases | Represent text as embeddings and store/query them in FAISS and Chroma. |
| RAG fundamentals | Build a retrieval-augmented pipeline that grounds an LLM on external data. |
| Advanced RAG | Improve retrieval with re-ranking, hybrid search and query transformation. |
| AI Agents fundamentals | Design agents that reason and use tools (ReAct, function calling). |
| LangChain | Compose LLM applications with chains, memory and tools. |
| LangGraph | Build stateful, multi-step agent workflows with explicit control flow. |
| MCP | Connect agents to external tools and data through the Model Context Protocol. |
| Multi-agent systems | Orchestrate multiple collaborating agents for complex tasks. |
| Evaluation of LLM apps | Measure quality with RAGAS and LLM-as-judge instead of relying on vibe-checks. |
| LLMOps & Deployment | Deploy, monitor and manage the cost/latency of LLM apps in production. |


## Requirements
* [Python](http://www.python.org) version >= 3.10;
* [LangChain](https://python.langchain.com), framework for building LLM applications;
* [LangGraph](https://langchain-ai.github.io/langgraph/), library for stateful, multi-step agents;
* [langchain-openai](https://python.langchain.com/docs/integrations/platforms/openai/), OpenAI integration for LangChain;
* [langchain-anthropic](https://python.langchain.com/docs/integrations/platforms/anthropic/), Anthropic/Claude integration for LangChain;
* [openai](https://github.com/openai/openai-python), the official OpenAI Python SDK;
* [anthropic](https://github.com/anthropics/anthropic-sdk-python), the official Anthropic (Claude) Python SDK;
* [chromadb](https://www.trychroma.com/), open-source embedding/vector database;
* [faiss-cpu](https://github.com/facebookresearch/faiss), library for efficient similarity search;
* [sentence-transformers](https://www.sbert.net/), embeddings for sentences and paragraphs;
* [tiktoken](https://github.com/openai/tiktoken), fast BPE tokenizer for OpenAI models;
* [ragas](https://docs.ragas.io/), evaluation framework for RAG pipelines;
* [python-dotenv](https://github.com/theskumar/python-dotenv), management of environment variables and API keys;
* [Jupyter](https://jupyter.org/), with the additional libraries required for the notebook interface.

A good, easy to install option that supports Mac, Windows, and Linux, and that has all of these packages (and much more) is the [Anaconda](https://www.anaconda.com/). All requirements are also listed in [`requirements.txt`](./requirements.txt).

You will need API keys to work with commercial LLMs. Copy [`.env.example`](./.env.example) to `.env` and fill in your `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`.

GIT!! Unfortunatelly out of the scope of this class, but please take a look at these [tutorials](https://help.github.com/articles/good-resources-for-learning-git-and-github/)

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
and branches. JSON, Markdown and HTML reports are retained for 14 days. The
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
summary; the `quality-reports` artifact retains detailed reports for 14 days.
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

### 1. Intro to LLMs & Prompt Engineering
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 1 | Introduction to Large Language Models & Prompt Engineering | [L1 - Intro to LLMs](./notebooks/L1-IntroToLLMs.ipynb) | |

### 2. Working with LLM APIs (OpenAI, Anthropic/Claude)
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 2 | Calling LLM APIs: OpenAI and Anthropic/Claude | | |

### 3. Embeddings & Vector Databases (FAISS, Chroma)
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 3 | Embeddings and Vector Databases with FAISS and Chroma | | |

### 4. RAG basics
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 4 | Retrieval-Augmented Generation fundamentals | | |

### 5. Advanced RAG (re-ranking, hybrid search, query transformation)
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 5 | Advanced RAG: re-ranking, hybrid search and query transformation | | |

### 6. AI Agents fundamentals (ReAct, tool use, function calling)
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 6 | AI Agents: ReAct, tool use and function calling | | |

### 7. LangChain
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 7 | Building LLM applications with LangChain | | |

### 8. LangGraph (stateful/multi-step agents)
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 8 | Stateful, multi-step agents with LangGraph | | |

### 9. MCP - Model Context Protocol
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 9 | Connecting tools and data with the Model Context Protocol | | |

### 10. Multi-agent systems
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 10 | Designing and orchestrating multi-agent systems | | |

### 11. Evaluation of LLM apps (LLM-as-judge, RAGAS)
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 11 | Evaluating LLM applications: LLM-as-judge and RAGAS | | |

### 12. LLMOps & Deployment
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 12 | LLMOps: deploying and monitoring LLM applications | | |

## Interest Links 🔗
Module | Topic | Material |
| :----| :----| :----|
| LangChain | Official Documentation | [LangChain Docs](https://python.langchain.com) |
| LangGraph | Official Documentation | [LangGraph Docs](https://langchain-ai.github.io/langgraph/) |
| MCP | Model Context Protocol | [modelcontextprotocol.io](https://modelcontextprotocol.io) |
| GenAI | Short Courses | [DeepLearning.AI Short Courses](https://www.deeplearning.ai/short-courses/) |

---

> 📚 This course is a proposed continuation ("part 2") of [Advanced Topics in Analytics](https://github.com/sergiomorapardo/AdvancedTopicsAnalytics), which covered MLOps, Deep Learning, NLP and Graph Learning.
