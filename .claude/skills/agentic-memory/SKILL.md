---
name: agentic-memory
description: Designs and builds an agent on Claude that remembers each conversation with LangGraph persistence (checkpointer, one thread_id per conversation, get_state, a search tool) and pauses before any action that moves money or writes until a person approves, edits or rejects it: interrupt() and Command(resume=...) in a graph, or HumanInTheLoopMiddleware on a tool. One decision at a time with ASCII diagrams, a blueprint, a run log, offline checks that count the action and one paid run after approval. Use it when answers depend on earlier turns or an action must wait for a person: "memory", "thread_id", "checkpointer", "interrupt", "human-in-the-loop", "aprobación humana", "que recuerde la conversación", "aprobar antes de desembolsar", /agentic-memory. Not for one question per run (use llm-rag), tools without memory (use llm-tools), routing or loops (use agentic-patterns) or measuring (use eval-experiments).
---

# Agent memory and human approval with LangGraph persistence

You and the person decide and write down: the **thread** (what one conversation or case is and where its `thread_id` comes from), the **checkpointer** (in memory for a notebook, a database for a service), the **tools** the agent searches with, so that each turn looks up fresh data instead of trusting what the thread remembers, and, when the app acts, the **approval**: which action writes, what the person sees in the pause and what they may edit. LangGraph saves the state of each thread after every step; the same checkpoint lets the graph stop with `interrupt()` and resume with `Command(resume=...)`.

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
| "Why does the agent forget?", "rewrite or let the agent search?", "which checkpointer?", "where does the person approve?" | `references/concepts.md` |
| Which piece to use, which files to generate, rules that are not negotiable | `references/build.md` |
| Offline checks, the paid run and the delivery | `references/validation.md` |
| An error symptom | `references/gotchas.md` |

Template to copy and fill (`TODO` marks): `assets/app.py`. Two files are copied as is next to every app: `references/examples/project.py` (the only code that knows the project: credentials, model, sample data) and `references/examples/run_log.py`.

## Verified examples

Read in full the example of the piece you are about to write. Copy the shape, change the content. Every example runs on its own from the repo root and imports its model from `project.py`; `references/project.md` says how they were verified.

| Piece | Example |
|---|---|
| The retriever as a `@tool`, `create_agent` with a checkpointer, one `thread_id` per conversation, `get_state` and the queries the agent wrote | `references/examples/memory_agent.py` |
| Human approval: a `StateGraph` whose limits in code decide who needs a person, pauses with `interrupt()`, resumes with `Command(resume=...)` (approve, edit or reject) and keeps the action in its own node; and `HumanInTheLoopMiddleware` on an agent's tool, with a check that a rejected call never ran | `references/examples/approval.py` |
| Local run log: `runs/<timestamp>/events.jsonl` + `transcript.md` | `references/examples/run_log.py` |

For one question per run or a fixed rewrite of each follow-up, hand over to llm-rag; for the tools themselves, to llm-tools; for routing, parallel branches or loops, to agentic-patterns (put the approval after them, as the graph in `approval.py` does after its validation).

## What is never skipped

1. **One decision per question**, with AskUserQuestion and an ASCII diagram in the `preview`. With "you decide" or no human: the recommended options.
2. **Smallest shape that works.** If each question is complete, no memory is needed: say so and hand over to llm-rag or llm-tools.
3. **Run log always.** Every run writes `runs/<timestamp>/events.jsonl` and `transcript.md`. Tracing services are optional and spend a shared budget.
4. **No paid call without an explicit "yes".** Before running, state how many model calls and traces the run makes, and wait.
5. **The model comes from `project.py`.** Never write a key in code; never switch to a bigger model on your own.
6. **Conversations are isolated.** One `thread_id` per conversation, taken from the session, never shared between people.
7. **Memory does not replace a fresh lookup** of data that changes, such as a balance: the agent looks it up again.
8. **No action without an answer.** Anything that disburses, writes or sends waits in an `interrupt()` or behind `HumanInTheLoopMiddleware`, runs only after the approval (in its own node, idempotent in a real system), and an offline check counts that it ran 0 times before the answer and once after it.
9. **Synthetic or anonymized data** only. No real customer data, PII or raw extracts.
10. **Not done without a successful run** and the transcript read, or an explicit note that it could not run and the exact command to run it.
