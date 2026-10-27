---
name: evaluate-app
description: Measures an LLM app that already exists, such as a RAG app, a chain, an agent or a LangGraph workflow, so that two versions can be compared with evidence. Builds a LangSmith dataset with references written by people, helps write code evaluators (including tool calls, arguments, routes and call budgets of agents) and LLM judges from rubrics, calibrates the judge against human labels, runs one experiment per configuration only after approval, then downloads runs, traces and scores and writes a report with the interpretation. Use when someone asks to evaluate, test, benchmark or compare an LLM app or two prompts, retrievers or models ("is the new version better?", "build a dataset", "write an evaluator", "LLM-as-a-judge", "OpenEvals", "LangSmith experiment", "analyze these experiments", /evaluate-app). Not for designing or building the app itself (use agentic-workflow) or for monitoring production traffic.
---

# Evaluate an LLM app

An evaluation answers one question with evidence: **which configuration should we keep, and what is still missing to decide?** You and the person fix what is compared, the questions with their references, how each answer is scored and what it will cost. One good example in a demo is not an evaluation.

This file is the map. Open each reference when you reach its phase, in full, and not before.

## Flow

Copy this checklist into your answer and tick it as you go:

```
- [ ] 0. Project            → read references/project.md (model, credentials, budget, paths)
- [ ] 1. Design              → read references/design.md (one decision per question)
- [ ] 2. Plan confirmed: configurations, dataset, evaluators, subset, cost
- [ ] 3. Evaluators          → read references/evaluators.md; code first, judges from rubrics
- [ ] 3b. Build              → copy references/examples/evaluation.py and adapt it
- [ ] 4. Offline checks      → read references/validation.md (no model, no LangSmith)
- [ ] 5. Calibration and experiments, only after an explicit "yes" with calls, traces and experiments
- [ ] 6. Results            → read references/results.md; download traces, report, interpretation
- [ ] 7. If something fails  → references/gotchas.md, fix only that, back to step 4
- [ ] 8. Delivery: tables, report path, links, and supported / hypothesis / not supported
```

## What to open and when

| Phase or question | Open |
|---|---|
| Model, credentials, LangSmith budget and naming, sample data | `references/project.md` |
| What to compare, where the references come from, how many questions | `references/design.md` |
| Writing a code evaluator or a judge rubric, calibrating it | `references/evaluators.md` |
| Evaluating an agent or a graph: tool calls, arguments, routes, plans, forbidden actions, call budget | `references/agents.md` |
| Downloading runs and traces, the report, interpreting the experiments | `references/results.md` |
| Offline checks and the paid run | `references/validation.md` |
| An error symptom | `references/gotchas.md` |

## Examples

| File | What it gives |
|---|---|
| `references/examples/evaluators.py` | Code evaluators (`retrieval_hit`, `citations_ok`, `figures_match`), `make_judge` to turn a rubric into an evaluator, `build_judge_model` and `calibrate` |
| `references/examples/agent_evaluators.py` | Code evaluators of what an agent or graph did (`tools_called`, `tool_args_match`, `no_forbidden_tool`, `route_correct`, `plan_covers`, `calls_within`) and `agent_outputs` to build their input from the messages |
| `references/examples/results.py` | Download the runs, traces and scores of experiments, compare them question by question with a sign test, diagnose retrieval vs generation and write `report.md` |
| `references/examples/evaluation.py` | The whole run on a RAG app: dataset created once, calibration that stops the run if the judge is not trusted, two experiments, and the report at the end |
| `references/examples/project.py` | The only file that knows the project: model, credentials, prices, sample data |

Copy the shapes and change the app under test, the configurations, the rubrics and the data.

## What is never skipped

1. **References come from people** who know the process, never from the model under test. Without references there is no "correct".
2. **Same examples, same evaluators** for every configuration. Change one thing at a time.
3. **Code evaluators first.** Add a judge only for what code cannot see, and calibrate it against human labels before trusting it. If they disagree, fix the rubric and calibrate again, before the experiments.
4. **A judge's format failure is not a bad answer.** It scores `None`, is counted apart and is read by hand.
5. **No paid run without an explicit "yes"** after stating model calls, traces and the new experiments it leaves. Each run adds experiments; deleting them needs the person's approval.
6. **Report the number of questions next to every average.** With 5 questions one answer moves 20 points: that is a signal to read the cases, not a proof.
7. **Quality, latency and cost** are reported together; the judge's own cost is part of the evaluation's cost.
8. **Synthetic or anonymized data** in datasets and references. Nothing raw or personal goes to LangSmith or the model.
