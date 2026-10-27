# The wizard, step by step

Run the design as a wizard. In each step use **AskUserQuestion**: one question, two to four options, the recommended one first with "(Recommended)", and a `preview` with an ASCII diagram of the graph with that option. Base diagrams are in `references/diagrams.md`: adapt them with the real names of the person's nodes. Before each question write one or two lines on what is decided and why it matters; after each answer confirm in one line what was settled.

Skip the steps the request already answers. If the person says "you decide", pick the recommended option in every step and continue. If AskUserQuestion is not available, ask the same question in text with numbered options and the diagram in a code block.

| Step | Question | Typical options | Diagram |
|---|---|---|---|
| 1 · Goal | Which sentence describes what the workflow must solve? | 2–3 one-sentence goals, from smallest to most ambitious. Recommend the smallest | "decision tree" |
| 2 · Is a pattern needed? | Can one call or one agent do it? | One chain or one agent: hand over to agentic-workflow (Recommended when it fits) · A pattern, because steps, routes, branches, approval or iteration are needed | "decision tree" |
| 3 · Pattern | Which shape do the steps have? | Fixed steps in order with an early stop (chaining) · Different treatment per type of input (routing) · Independent checks or subtasks at the same time (parallelization) · The number of subtasks depends on the input (orchestrator-workers) · Correct until explicit criteria pass (evaluator-optimizer). Recommend the first that fits | the pattern's diagram |
| 4 · State | What must every step see, and what does each step add? | Propose a `TypedDict` with one field per input and per step output; mark lists that several nodes fill in parallel with a reducer (`Annotated[list, operator.add]`) | "state" |
| 5 · Decisions in code | Which decisions must never be left to the model? (multiSelect) | A gate that stops early (Recommended for chaining) · Routes as a `Literal` (Recommended for routing) · An aggregator rule (Recommended for parallel) · A cap on attempts (always for loops) · Limits on amounts or counts · Rules code can count (length, format, figures) checked before any judge | "code or model" |
| 6 · Person in the loop | Does any step act outside the graph (move money, send, publish, delete)? | No: read only (Recommended when true) · Yes: `interrupt` in a node, with approve/reject/edit and a checkpointer · Yes, on an agent's tool: `HumanInTheLoopMiddleware` | "approval" |
| 7 · Per-pattern details | Only the questions of the chosen pattern, below | | |
| 8 · Observability | How do we see what happened? | Local run log only (Recommended) · Run log + LangSmith traces (counted against the budget and approved before each run) | — |

## Per-pattern questions (step 7)

- **Chaining**: which steps, in order; what each returns (structured output when the next step reads fields); where the gate goes and what the early exit answers without the model.
- **Routing**: the list of routes with one sentence each (it becomes the `Field` description); the specialist's prompt and context per route; a set of 3–5 questions with the route a person expects, at least one that a keyword rule gets wrong.
- **Parallelization**: one criterion per branch; each prompt says to judge only its criterion; the aggregator rule (all must approve, majority, any).
- **Orchestrator-workers**: what a task contains (question + which source); what the worker does, as a subgraph; what happens with an empty plan; the plan a person expects for one sample input.
- **Evaluator-optimizer**: the rubric, point by point; which points code can check (length, citations, figures) and which need the judge; the cap (3 by default); what is returned when the cap is reached without approval.
- **Approval**: which action, the thresholds that need a person, the options (approve, reject, edit), what the person sees to decide, and where the `thread_id` comes from.

Close the wizard with a **blueprint** before writing code: an ASCII diagram of the final graph with its nodes and edges, the state fields with their reducers, the decisions in code, the approval points, the list of files to create and the cost of one run per path (model calls and traces). Ask for confirmation with a last AskUserQuestion: "Build it like this (Recommended)" · "Change something".

## Use the diagrams to explain too

When the person asks "which pattern do I need?", "why does the list need a reducer?", "why a cap?", answer with the matching diagram from `references/diagrams.md` and the table in `references/concepts.md`, grounded in their workflow. On delivery, draw the blueprint again with what was actually built.
