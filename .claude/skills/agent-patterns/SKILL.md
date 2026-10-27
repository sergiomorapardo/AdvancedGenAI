---
name: agent-patterns
description: Wizard that designs and builds a LangGraph workflow on Claude when one chain or one agent is not enough: prompt chaining with a gate in code, routing to specialists, parallel reviewers with a reducer, human approval with interrupt or HumanInTheLoopMiddleware, orchestrator-workers with Send and subgraphs, and an evaluator-optimizer loop with a cap. Asks one decision at a time with ASCII diagrams, starts from the simplest pattern, checks the graph with fake models and runs it once only after approval. Use when someone asks for a StateGraph, a multi-step workflow, a router, parallel branches, fan-out/fan-in, a human approval step, pause and resume, an orchestrator, subgraphs, Send, reducers or a loop that corrects an answer ("which pattern do I need?", "interrupt", /agent-patterns). Not for one chain, tool agent, RAG or memory (agentic-workflow), measuring it (evaluate-app) or serving it (deploy-app).
---

# Agentic patterns with LangGraph

You and the person decide which **pattern** solves the problem, what lives in the **state**, which decisions belong to **code** and which to the model, and where a **person** must approve. Start from the simplest shape: one call, then a chain, then a pattern. Every extra step costs calls, latency and places to fail.

This file is the map. Each phase lives in `references/`: open the file of the phase when you reach it, in full, and not before.

## Flow

Copy this checklist into your answer and tick it as you go:

```
- [ ] 0. Project            → read references/project.md (model, credentials, paths, budget)
- [ ] 1. Wizard              → read references/wizard.md and references/diagrams.md
- [ ] 2. Blueprint confirmed by the person (graph, state, controls in code, cost per run)
- [ ] 3. Build               → read references/build.md + the example of the chosen pattern
- [ ] 4. Offline checks      → read references/validation.md (fake models, no paid calls)
- [ ] 5. One paid run, only after an explicit "yes" with the call and trace count
- [ ] 6. If something fails  → references/gotchas.md, fix only that, back to step 4
- [ ] 7. Delivery with paths, command, receipt and final graph
```

## What to open and when

| Phase or question | Open |
|---|---|
| Model, credentials, where graphs live, budget, controls this project enforces | `references/project.md` |
| Running the wizard: what to ask, which options | `references/wizard.md` |
| ASCII diagrams for the `preview` fields and for explaining a pattern | `references/diagrams.md` |
| "Which pattern?", "code or model?", "why a reducer?", "why a cap?", "when is a person needed?" | `references/concepts.md` |
| Which pieces to write, which files to generate, rules that are not negotiable | `references/build.md` |
| Offline checks with fake models, the paid run and the delivery | `references/validation.md` |
| An error symptom | `references/gotchas.md` |

Template to copy and fill (`TODO` marks): `assets/graph.py`. Two files are copied as is next to every graph: `references/examples/project.py` (the only code that knows the project: credentials, model, sample policies) and `references/examples/run_log.py`.

## Verified examples

Read in full the example of the pattern you are about to write. Copy the shape, change the content. Every example runs on its own from the repo root, builds its graph from a `build_*(model)` function so the tests can pass a fake model, and imports its model from `project.py`.

| Pattern | Example |
|---|---|
| Prompt chaining: fixed steps, structured output between them, a gate in code that stops early | `references/examples/graph_chain.py` |
| Routing: a classifier with a `Literal` route, one specialist per route with its own prompt and policy, the keyword rule it replaces, a route check | `references/examples/graph_router.py` |
| Parallelization: fan-out to reviewers with one criterion each, a list reducer, an aggregator in code | `references/examples/graph_parallel.py` |
| Human approval: `interrupt` + checkpointer + `Command(resume=...)` with approve, reject or edit, and `HumanInTheLoopMiddleware` on an agent's tool | `references/examples/approval.py` |
| Orchestrator-workers: a structured plan, `Send` per task, the worker as a subgraph, an empty-plan path, a plan check | `references/examples/orchestrator.py` |
| Evaluator-optimizer: generate, evaluate with a rubric, feedback back, a cap in code, and the rules code can count kept out of the judge | `references/examples/evaluator_loop.py` |
| Local run log: `runs/<timestamp>/events.jsonl` + `transcript.md` | `references/examples/run_log.py` |

If the problem is solved by one chain, one tool agent, RAG or memory, hand over to the agentic-workflow skill. To measure the graph on a dataset (routes, tool calls, answers), hand over to the evaluate-app skill. To serve it behind an API with persistent threads, hand over to the deploy-app skill.

## What is never skipped

1. **One decision per question**, with AskUserQuestion and an ASCII diagram in the `preview`. With "you decide" or no human: the recommended options.
2. **Simplest pattern that works.** Say it when a chain or one agent would do; a pattern needs a reason the person agrees with.
3. **Controls in code.** Gates, limits, routes that must not be invented (`Literal`), caps on loops and approval of irreversible actions are code, never only a prompt.
4. **Every loop ends.** A counter in the state and a condition that reads it.
5. **No irreversible action without a person.** Moving money, sending, publishing or deleting goes through `interrupt` or `HumanInTheLoopMiddleware`, with a checkpointer so the graph can resume.
6. **Run log always.** Every run writes `runs/<timestamp>/events.jsonl` and `transcript.md`.
7. **No paid call without an explicit "yes".** Before running, state the model calls per path and the traces, and wait.
8. **The model comes from `project.py`.** Never write a key; never switch to a bigger model on your own.
9. **Synthetic or anonymized data** only.
10. **Not done without a successful run** and the transcript read, or an explicit note that it could not run and the exact command.
