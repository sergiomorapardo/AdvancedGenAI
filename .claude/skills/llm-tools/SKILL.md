---
name: llm-tools
description: Designs and builds a tool-using agent on Claude with LangChain: read-only @tool functions, a public HTTP API, create_agent with an answer check, or the tools of MCP servers via MCPAdapter, with the pause when a server asks the person. One decision at a time with ASCII diagrams, a blueprint, a run log, offline checks and one paid run after approval. Use it whenever the model must look data up before answering (a balance, an exchange rate, an API), even if nobody says agent: "build an agent", "@tool", "create_agent", "tool calling", "MCPAdapter", "MCP tools", "elicitation", "hazme un agente", "que consulte la cartera", "conectar una API", "usar las herramientas del servidor MCP", /llm-tools. Not for building an MCP server (use mcp-server), documents (use llm-rag), memory or human approval (use agentic-memory), LangGraph patterns (use agentic-patterns) or measuring an app (use eval-experiments).
---

# Tools and agents with LangChain

You and the person decide three things and write them down: the **tools** (what the model can look up, and how: a function over a table, a public API, the tools of an MCP server), the **agent** (its system prompt and the check of its answer) and the **guardrails** (what the code enforces, whatever the model asks). LangChain runs the loop: model → tool → model, until the model answers in text.

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
| "Chain or agent?", "tool or prompt?", "tool or documents?", "MCP or a @tool?" | `references/concepts.md` |
| Which piece to use, which files to generate, rules that are not negotiable | `references/build.md` |
| Offline checks, the paid run and the delivery | `references/validation.md` |
| An error symptom | `references/gotchas.md` |

Template to copy and fill (`TODO` marks): `assets/app.py`. Two files are copied as is next to every app: `references/examples/project.py` (the only code that knows the project: credentials, model, sample data) and `references/examples/run_log.py`.

## Verified examples

Read in full the example of the piece you are about to write. Copy the shape, change the content. Every example runs on its own from the repo root and imports its model from `project.py`; `references/project.md` says how they were verified.

| Piece | Example |
|---|---|
| A read-only `@tool`, errors as data, `create_agent` and an answer check | `references/examples/tools_agent.py` |
| A tool over a public HTTP API: timeout, `not_found`/`unavailable` as data, source named | `references/examples/api_tool.py` |
| Tools from MCP servers: `MCPAdapter` with the `mcpServers` configuration, prefixed tool names, async `ainvoke`, and the pause and resume when a server asks the person (elicitation) | `references/examples/mcp_agent.py` |
| Local run log: `runs/<timestamp>/events.jsonl` + `transcript.md` | `references/examples/run_log.py` |

To build or review the MCP server itself, hand over to the mcp-server skill. For fixed steps, to llm-prompts; for answers from documents, to llm-rag; for a conversation that remembers or an action that waits for a person, to agentic-memory; for a gate between steps, routing, parallel branches or a loop, to agentic-patterns.

## What is never skipped

1. **One decision per question**, with AskUserQuestion and an ASCII diagram in the `preview`. With "you decide" or no human: the recommended options.
2. **Smallest shape that works.** If the steps are fixed and known, it is a chain, not an agent: say so in the goal step and hand over to llm-prompts.
3. **Run log always.** Every run writes `runs/<timestamp>/events.jsonl` and `transcript.md`. Tracing services are optional and spend a shared budget.
4. **No paid call without an explicit "yes".** Before running, state how many model calls and traces the run makes, and wait.
5. **The model comes from `project.py`.** Never write a key in code; never switch to a bigger model on your own.
6. **Tools are read only** unless the person decides otherwise; outward actions (send, publish, buy, reserve) stay as drafts that need human approval.
7. **The answer uses the tool's figures**, and a code check confirms it against the `ToolMessage`.
8. **Synthetic or anonymized data** only. No real customer data, PII or raw extracts.
9. **Not done without a successful run** and the transcript read, or an explicit note that it could not run and the exact command to run it.
