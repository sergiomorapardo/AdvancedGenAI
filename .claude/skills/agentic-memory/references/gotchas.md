# Gotchas: symptom → cause → fix

Observed with `langchain` 1.4, `langchain-anthropic` 1.7 and `claude-haiku-5-5`.

| Symptom | Cause | Fix |
|---|---|---|
| 400 error mentioning `temperature` | Haiku 5.5 rejects it | Remove `temperature` |
| Empty or cut answer with `max_tokens=400` | Default reasoning spends the token budget | `thinking={"type": "disabled"}` |
| 400 error about prefill or the final assistant message | The conversation sent to the model ends in an AI message | Send a list that ends in a human or tool message; keep the reply apart (`conversation = messages + [response]`) |
| The agent forgets the previous turn | No checkpointer, or a different `thread_id` | `create_agent(..., checkpointer=...)` and the same `config` on every turn |
| The agent answers a follow-up without searching | The fragments of the first turn are in the thread as `tool` messages | Normal; a new topic makes it search again. State a range of calls |
| The memory is gone after restarting | `InMemorySaver` lives in the process | Use a database checkpointer for a service; rerun the conversation in a notebook |
| An action ran twice after approval | Code before `interrupt` in the same node ran again on resume | Move the action to a node after the approval |
| The agent's tool ran without approval | The tool name in `interrupt_on` does not match | Use the exact tool name; check with a rejected request that no `ToolMessage` appears |
| `KeyError: '__interrupt__'` | The request did not reach the approval (amount below the limit, or the model did not call the tool) | Check `"__interrupt__" in state` before reading it |
| Two traces for one approval | Pause and resume are two top-level invokes | Expected; count them in the budget |
| The agent stops with `__interrupt__` in the state | A server asked the person (elicitation) | Show the question, resume with `Command(resume={"responses": {key: answer}})` and the same `thread_id` |
| `RuntimeError: Cannot use Command(resume=...) without checkpointer` | The agent paused for an elicitation but has nowhere to keep its state | `create_agent(..., checkpointer=InMemorySaver())` and the same `thread_id` on the pause and the resume |
| The action ran twice, or before the approval | It sits in the node that calls `interrupt()`, which runs again from its first line on resume | Move it to its own node after the gate and key it by the case id so a repeat does nothing |
| `KeyError` when resuming, or the resume does nothing | `Command(resume=...)` went to another `thread_id`, which has no pause | Read `get_state(config).next` first; resume on the thread that paused |
| `Command(resume={})` pauses again | An empty dict is read as a map of interrupt ids with no answers | Send the answer as a dict with at least `decision` |
| A paused node shows `interrupted` in LangSmith | That is how a pause is recorded; the root ends in success | Normal: the resume is a second trace with the same `thread_id` |
| The agent answers in English to a Spanish thread without context | The system prompt does not fix the language | Add "answer always in <language>" to the system prompt |
