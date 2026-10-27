# Gotchas: symptom → cause → fix

Observed with `langgraph` 1.2, `langchain` 1.4, `langchain-anthropic` 1.7 and `claude-haiku-5-5`.

| Symptom | Cause | Fix |
|---|---|---|
| `InvalidUpdateError: ... can receive only one value per step` | Several parallel nodes write the same field without a reducer | `Annotated[list[...], operator.add]` on that field |
| A list loses the items of earlier nodes | The field has no reducer, so each update replaces it | Add the reducer, or return the whole list on purpose |
| A node's update erases other fields | The node returned the whole state with a changed copy | Return only the fields it changes |
| The router returns a route that has no node | The route is a plain `str` | `Literal[...]` in the schema and in the function that reads it |
| The keyword rule sends "Me quedé sin plata" to the wrong specialist | The rule sees words, not meaning | Use the router; keep the rule only as a baseline to compare |
| Reviewers with different criteria all reject for the same content error | Each prompt let the reviewer judge everything | Say in each prompt to judge only its criterion and ignore the others |
| The graph ends without an answer after the plan | `Send` with an empty list launches no worker and nothing reaches the synthesizer | `return [Send(...) ...] or "synthesize"` and list both targets in `add_conditional_edges` |
| A worker cannot see `message` | `Send` passes only the task: the worker's state is what you send | Put in the task everything the worker needs |
| The plan sends a question to the wrong policy | The `Field` description of the source is vague | Describe each source by its topics; check the plan with `check_plan` |
| The loop never ends, or stops with `GraphRecursionError` | No cap, or the cap is not read by the condition | `attempts` in the state, incremented by the generator, read by `should_continue` |
| The judge approves an answer that breaks a countable rule | A model is not a counter | Count length, format and citations in code before calling the judge |
| The loop always ends at the cap because the answer stays a few words over the limit | Models do not count words, even with the count in the feedback (seen with `claude-haiku-5-5`: 112 → 96 → 96 words for a limit of 90) | Keep the count in code and leave margin in the limit, or trim in code what can be trimmed; report when the cap was reached |
| The judge's structured output fails or comes truncated | Not enough tokens to reason and answer | `max_tokens=1000` and `method="json_schema"` for the judge |
| `RuntimeError: Cannot use Command(resume=...) without checkpointer` | The graph was compiled without one: it can pause, but not resume | `compile(checkpointer=InMemorySaver())` (a database checkpointer in a service) |
| The resume starts a new run instead of continuing | A different `thread_id`, or a new graph object with a new in-memory checkpointer | Same graph object and the same `config` on pause and resume |
| An action ran twice after approval | Code before `interrupt` in the same node ran again on resume | Move the action to a node after the approval |
| The agent's tool ran without approval | The tool name in `interrupt_on` does not match | Use the exact tool name; check with a rejected request that no `ToolMessage` appears |
| `KeyError: '__interrupt__'` | The request did not reach the approval (amount below the limit, or the model did not call the tool) | Check `"__interrupt__" in state` before reading it |
| Two traces for one approval | Pause and resume are two top-level invokes | Expected; count them in the budget |
| `stream_mode="updates"` shows `None` for a node | The node returned nothing | Return `{}` explicitly, or the fields it changes |
