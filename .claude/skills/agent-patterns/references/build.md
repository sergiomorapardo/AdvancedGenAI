# Build: pieces, files and rules

## Contents

- Which piece to use
- Files to generate
- Rules that are not negotiable

## Which piece to use

- **State** (all examples): a `TypedDict` with `total=False`; one field per input and per step output. A field written by several nodes in the same step is `Annotated[list[...], operator.add]`.
- **Nodes**: plain functions `state -> dict` that return only the fields they change. Put the model in a closure: `build_<graph>(model)` defines the nodes and returns `builder.compile()`, so the tests pass a fake model and the script passes `build_model()`.
- **Gate** (`graph_chain.py`): `add_conditional_edges("classify", gate)` where `gate` returns a node name annotated with `Literal[...]`. The early exit answers a fixed text, without the model.
- **Router** (`graph_router.py`): `with_structured_output(RouteDecision)` where `route: Literal[...]` and the `Field` description defines each route in one line; `add_conditional_edges("router", lambda state: state["route"])`; one specialist node per route built by a factory function. Keep the keyword rule only to show what the router replaces, and `check_routes` for the route test.
- **Parallel branches** (`graph_parallel.py`): `add_edge(START, name)` and `add_edge(name, "aggregate")` for each branch; each reviewer returns `{"reviews": [ {...} ]}`; the aggregator is code. Each reviewer prompt names its criterion and says to ignore the others.
- **Approval in a graph** (`approval.py`): a node that calls `interrupt({...})` with what the person needs to decide, and returns `Command(goto=..., update=...)` per decision. `compile(checkpointer=...)`, `config={"configurable": {"thread_id": ...}}`, `graph.get_state(config).next` to show where it stopped, `graph.invoke(Command(resume=answer), config)` to continue. Actions happen in the node after the approval, never before `interrupt`.
- **Approval on an agent's tool** (`approval.py`): `create_agent(..., middleware=[HumanInTheLoopMiddleware(interrupt_on={"tool_name": True})], checkpointer=...)`; read `state["__interrupt__"][0].value["action_requests"]`; resume with `Command(resume={"decisions": [{"type": "approve"}]})`, `{"type": "edit", ...}` or `{"type": "reject", "message": ...}`. Check in the messages that a rejected tool never ran.
- **Orchestrator-workers** (`orchestrator.py`): `with_structured_output(Plan)` with `tasks: list[Task]`; `add_conditional_edges("orchestrator", assign_workers, ["worker", "synthesize"])` where `assign_workers` returns `[Send("worker", task) ...] or "synthesize"`; the worker is a compiled subgraph added as one node; workers write to a list with `operator.add`. `check_plan` compares the sources used with the expected ones.
- **Evaluator-optimizer** (`evaluator_loop.py`): `attempts` in the state, incremented by `generate`; `should_continue` returns `END` when approved or at `MAX_ATTEMPTS`; the judge is `with_structured_output(Feedback, method="json_schema")` with more tokens; rules code can count (length, format, citations) are checked in `evaluate` before calling the judge; `history` keeps every attempt.
- **Streaming the steps**: `graph.stream(inputs, config, stream_mode="updates")` yields `{node: update}` per step.
- **Run log** (`run_log.py`): copy it as is and pass `config={"callbacks": [run_log]}` (together with `configurable` when there is a `thread_id`). Print `run_log.receipt()` at the end.

## Files to generate

Copy `assets/graph.py`, fill the `TODO` marks and delete the pieces the blueprint does not use. Output structure, in a new folder named after the graph:

```
labs/<graph-name>/
  README.md        # problem, the graph as ASCII, decisions in code, how to run, cost per path
  graph.py         # from assets/graph.py
  project.py       # copied as is from references/examples/project.py
  run_log.py       # copied as is from references/examples/run_log.py
  .gitignore       # runs/
  runs/<timestamp>/
```

## Rules that are not negotiable

1. **Model**: `build_model(max_tokens=...)` from `project.py`; nothing else creates a chat model. Never a bigger model on your own.
2. **Credentials** only through `project.py`. Never write a key, never print `.env`.
3. **Every loop has a cap** in the state and a condition that reads it.
4. **Routes, gates, limits and aggregator rules are code.** The model never decides alone whether a rule holds.
5. **Irreversible actions need approval** through `interrupt` or `HumanInTheLoopMiddleware`, with a checkpointer and one `thread_id` per request. Code before `interrupt` must have no side effects: it runs again on resume.
6. **Run log always**; tracing off by default.
7. **Synthetic data** (amounts, customers, messages) with one or two traps that exercise each path: a message the gate stops, a question a keyword rule misroutes, an amount above each limit, a draft that breaks the rubric.
8. **Names in English** for files, functions, classes, nodes and state fields.
9. **Keep it simple**: no node, field or branch the blueprint does not need.
