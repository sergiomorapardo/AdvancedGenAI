# Check, run and deliver

## 1. Offline checks (no paid calls)

Run them before asking for the paid run:

```
uv run python -c "import ast, pathlib; ast.parse(pathlib.Path('labs/<graph-name>/graph.py').read_text())"
uv run --locked ruff check labs/<graph-name>
```

Then, in a short `uv run python` snippet that imports `graph` without calling `main()`:

1. **Shape**: `build_<graph>(fake_model).get_graph()` has the nodes and edges of the blueprint; print `draw_ascii()` and compare it with the blueprint.
2. **Code decisions**: call the gate, the route function, the aggregator, `assign_workers` and `should_continue` directly with hand-written states, one per branch, including the edge cases (empty plan, cap reached, amount on each limit).
3. **Each path with a fake model**: `GenericFakeChatModel(messages=iter([...]))` returns fixed `AIMessage`s; for structured output, give the fake a `with_structured_output` that returns the Pydantic objects you choose (see `tests/test_agent_patterns.py`). Run every path and check the final state and the number of model calls.
4. **Reducers**: in a parallel or Send graph, every branch's item is in the list at the end.
5. **Approval**: the graph pauses with the expected `__interrupt__` value; `get_state(config).next` names the approval node; resuming with each option gives the expected final state; a rejected agent tool never produced a `ToolMessage`.
6. **Loop**: with a fake judge that never approves, the loop stops at the cap and `history` has one entry per attempt.

None of these call the paid model or create traces.

## 2. The paid run

Before running, tell the person exactly: the command, the model calls per path (see the example's docstring and `references/concepts.md`), the traces (0 with tracing off; otherwise 1 per top-level invoke, and pause and resume count as two) and the model. In this project the harness also asks before the command runs (`references/project.md`). Wait for an explicit "yes". A "yes" covers that run only.

```
uv run python labs/<graph-name>/graph.py
```

Check, in this order:

1. The receipt line: model calls and tokens are in the expected range.
2. The path: with `stream_mode="updates"` or the transcript, every node you expected ran, in order, and no other.
3. The decisions: the route, the plan, the reviewers' verdicts and the loop's attempts are what a person expects for the sample inputs (`check_routes`, `check_plan`, `history`).
4. `runs/<timestamp>/` exists with `events.jsonl` and `transcript.md`; open the transcript and read it.

If a check fails: look up the symptom in `references/gotchas.md`, fix only that, run the offline checks again and ask before the next paid run. If it cannot run (no key, no network), say so and leave the exact command.

## 3. Delivery

Answer with: the file paths, the command, the path of `transcript.md`, the receipt (model calls, tokens), the graph as ASCII with what was built, the decisions that live in code, and a single next step: measure the routes or answers with the evaluate-app skill, or serve the graph with the deploy-app skill.
