---
name: llm-prompts
description: Designs and builds a fixed-step LLM chain on Claude with LangChain: a chat prompt or a versioned Jinja template with StrictUndefined, the model and structured output with Pydantic. One decision at a time with ASCII diagrams, a blueprint, a run log, offline checks and one paid run after approval. Use it whenever the task is fixed steps over an input text (summarize, classify, extract fields, fill a template), even if nobody says chain: "chain", "ChatPromptTemplate", "Jinja", "structured output", "Pydantic", "hazme una cadena", "plantilla del prompt", "que devuelva un JSON con los campos", "extraer los datos del ticket", "¿cadena o agente?", /llm-prompts. Not for agents that look data up (use llm-tools), documents (use llm-rag), memory or human approval (use agentic-memory), LangGraph patterns (use agentic-patterns) or measuring an app (use eval-experiments).
---

# Prompts and chains with LangChain

You and the person decide three things and write them down: the **shape** (a chain with fixed steps, or a hand over when the model must fetch data), the **prompt** (inline or a versioned Jinja template) and the **output** (free text or fields that code reads). Most first apps are a chain: one call, predictable cost, easy to test.

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
| "Chain or agent?", "why Jinja?", "why structured output?" | `references/concepts.md` |
| Which piece to use, which files to generate, rules that are not negotiable | `references/build.md` |
| Offline checks, the paid run and the delivery | `references/validation.md` |
| An error symptom | `references/gotchas.md` |

Template to copy and fill (`TODO` marks): `assets/app.py`. Two files are copied as is next to every app: `references/examples/project.py` (the only code that knows the project: credentials, model, sample data) and `references/examples/run_log.py`.

## Verified examples

Read in full the example of the piece you are about to write. Copy the shape, change the content. Every example runs on its own from the repo root and imports its model from `project.py`; `references/project.md` says how they were verified.

| Piece | Example |
|---|---|
| Chain: chat template, model, structured output | `references/examples/chain.py` |
| Same, plus a versioned Jinja template with `StrictUndefined` | `references/examples/jinja_prompt.py` + `prompts/ticket.jinja` |
| Local run log: `runs/<timestamp>/events.jsonl` + `transcript.md` | `references/examples/run_log.py` |

If the steps depend on data the model must fetch, hand over to the llm-tools skill; for answers from documents, to llm-rag; for a conversation that remembers or an action that waits for a person, to agentic-memory; for a gate between steps, routing, parallel branches or a loop, to agentic-patterns.

## What is never skipped

1. **One decision per question**, with AskUserQuestion and an ASCII diagram in the `preview`. With "you decide" or no human: the recommended options.
2. **Smallest shape that works.** If the steps are fixed and known, it is a chain, not an agent: say so in the goal step.
3. **Run log always.** Every run writes `runs/<timestamp>/events.jsonl` and `transcript.md`. Tracing services are optional and spend a shared budget.
4. **No paid call without an explicit "yes".** Before running, state how many model calls and traces the run makes, and wait.
5. **The model comes from `project.py`.** Never write a key in code; never switch to a bigger model on your own.
6. **The user message is data.** Render the system prompt with Jinja; the user's text goes in its own human message, never through Jinja.
7. **Synthetic or anonymized data** only. No real customer data, PII or raw extracts.
8. **Not done without a successful run** and the transcript read, or an explicit note that it could not run and the exact command to run it.
