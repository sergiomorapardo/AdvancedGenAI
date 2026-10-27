---
name: agentic-workflow
description: Wizard that designs and builds an LLM app with LangChain and LangGraph on Claude: a fixed-step chain, a tool-using agent, a RAG app that cites its documents, a conversation that remembers follow-up questions, or an agent that uses the tools of MCP servers. Asks one decision at a time with AskUserQuestion and ASCII diagrams, shows a blueprint, generates the app with a local run log, checks it without the model and runs it once only after approval. Use when someone asks to create, design or brainstorm an agent, a chain or an agentic workflow ("build an agent", "make me an assistant that...", "create_agent", "LangGraph", "answer from these PDFs", "RAG", "FAISS", "Chroma", "follow-up questions", "chat memory", "MCP tools", "MCPAdapter", /agentic-workflow), or asks whether they need a chain, an agent, a tool, a Jinja template, RAG, query rewriting or a checkpointer. Not for measuring an existing app with datasets and judges (use evaluate-app) or for Claude Agent SDK projects.
---

# Agentic workflow with LangChain

You and the person decide four things and write them down: the **shape** (chain or agent), the **prompt** (inline or a versioned Jinja template), the **data and tools** (what the model can read, and how: a tool for tables and APIs, RAG for documents, history or a checkpointer for conversations) and the **guardrails** (what the code enforces, whatever the model asks). LangChain runs the loop; LangGraph comes in when the flow needs explicit state.

This file is the map. Each phase lives in `references/`: open the file of the phase when you reach it, in full, and not before.

## Flow

Copy this checklist into your answer and tick it as you go:

```
- [ ] 0. Project            → read references/project.md (model, credentials, paths, budget)
- [ ] 1. Wizard              → read references/wizard.md and references/diagrams.md
- [ ] 2. Blueprint confirmed by the person
- [ ] 3. Build               → read references/build.md + the example of each chosen piece
- [ ] 4. Offline checks      → read references/validation.md (no model calls)
- [ ] 5. One paid run, only after an explicit "yes" with the call and trace count
- [ ] 6. If something fails  → references/gotchas.md, fix only that, back to step 4
- [ ] 7. Delivery with paths, command, receipt and final blueprint
```

## What to open and when

| Phase or question | Open |
|---|---|
| Model, credentials, where apps live, budget, controls this project enforces | `references/project.md` |
| Running the wizard: what to ask, which options | `references/wizard.md` |
| ASCII diagrams for the `preview` fields and for explaining concepts | `references/diagrams.md` |
| "Chain or agent?", "tool or prompt?", "tool or documents?", "why Jinja?", "why structured output?", "rewrite or let the agent search?" | `references/concepts.md` |
| Which piece to use, which files to generate, rules that are not negotiable | `references/build.md` |
| Offline checks, the paid run and the delivery | `references/validation.md` |
| An error symptom | `references/gotchas.md` |

Template to copy and fill (`TODO` marks): `assets/app.py`. Two files are copied as is next to every app: `references/examples/project.py` (the only code that knows the project: credentials, model, sample corpus) and `references/examples/run_log.py`.

## Verified examples

Read in full the example of the piece you are about to write. Copy the shape, change the content. Every example runs on its own from the repo root and imports its model from `project.py`; `references/project.md` says how they were verified.

| Piece | Example |
|---|---|
| Chain: chat template, model, structured output | `references/examples/chain.py` |
| Same, plus a versioned Jinja template with `StrictUndefined` | `references/examples/jinja_prompt.py` + `prompts/ticket.jinja` |
| A read-only `@tool`, errors as data, `create_agent` and an answer check | `references/examples/tools_agent.py` |
| A tool over a public HTTP API: timeout, `not_found`/`unavailable` as data, source named | `references/examples/api_tool.py` |
| RAG: PDF pages with file and page, fragments, local embeddings, `@chain` with `[file, p. N]` citations, "not in the documents" and a citation check | `references/examples/rag.py` |
| A persistent index: FAISS (`save_local`/`load_local`) or Chroma (stable ids, metadata filter, cosine) | `references/examples/vector_store.py` |
| Conversational RAG: rewrite the follow-up with the history before retrieving, history in the answer, multi-query with a union of fragments | `references/examples/conversational_rag.py` |
| The retriever as a `@tool`, `create_agent` with a checkpointer, one `thread_id` per conversation, `get_state` and the queries the agent wrote | `references/examples/memory_agent.py` |
| Tools from MCP servers: `MCPAdapter` with the `mcpServers` configuration, prefixed tool names, async `ainvoke`, and the pause and resume when a server asks the person (elicitation) | `references/examples/mcp_agent.py` |
| Local run log: `runs/<timestamp>/events.jsonl` + `transcript.md` | `references/examples/run_log.py` |

To build or review the MCP server itself, hand over to the mcp-server skill. If the person needs a piece that is not in this table (a LangGraph graph with routing or parallel branches, human approval, orchestrator-workers, subgraphs), say so, check `references/project.md` for where the project covers it, and build the closest verified shape instead of improvising one. To measure the app on a dataset, hand over to the evaluate-app skill.

## What is never skipped

1. **One decision per question**, with AskUserQuestion and an ASCII diagram in the `preview`. With "you decide" or no human: the recommended options.
2. **Smallest shape that works.** If the steps are fixed and known, it is a chain, not an agent: say so in the goal step.
3. **Run log always.** Every run writes `runs/<timestamp>/events.jsonl` and `transcript.md`. Tracing services are optional and spend a shared budget.
4. **No paid call without an explicit "yes".** Before running, state how many model calls and traces the run makes, and wait.
5. **The model comes from `project.py`.** Never write a key in code; never switch to a bigger model on your own.
6. **Tools are read only** unless the person decides otherwise; outward actions (send, publish, buy, reserve) stay as drafts that need human approval.
7. **Synthetic or anonymized data** only. No real customer data, PII or raw extracts. Documents for RAG too: embeddings stay local by default, so documents do not leave the machine to be indexed.
8. **Answers from documents cite file and page**, and a code check confirms every citation was retrieved.
9. **Not done without a successful run** and the transcript read, or an explicit note that it could not run and the exact command to run it.
