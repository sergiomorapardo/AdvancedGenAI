# Check, run and deliver

## 1. Offline checks (no model calls)

Run them before asking for the paid run:

```
uv run python -c "import ast, pathlib; ast.parse(pathlib.Path('labs/<app-name>/app.py').read_text())"
uv run --locked ruff check labs/<app-name>
```

Then, in a short `uv run python` snippet that imports `app` without calling `main()`:

1. **Threads** (no model): run the agent with `GenericFakeChatModel` and two `thread_id`s; `get_state` shows each thread keeps only its own messages, and the second turn of the first thread sees the first.
2. **Searches** (no model): the queries the fake model wrote reach the tool unchanged, and a follow-up query is a complete question.
3. **Approval** (no model), if the app acts: count the calls of the action node (`disburse` in `approval.py`; wrap it before building the graph). It must run 0 times after the pause, after a new `invoke` without `Command`, after `Command(resume=...)` on another thread and after reject; and exactly once after approve or edit. Also check that `get_state(config).next` names the approval node while paused, that amounts below or above the limits never pause, and, for the agent, with a fake model that proposes the call, that a reject leaves no `ToolMessage` (`tool_executed`).

None of these call the model or create traces (`tool.invoke` creates a trace only if LangSmith is on).

## 2. The paid run

Before running, tell the person exactly: the command, the number of model calls (about 2 per turn that searches, 1 if the agent answers with what the thread already has; state a range; the approval graph makes none, the approval agent about 2 per request), the traces (0 with tracing off; otherwise 1 per top-level invoke, and pause and resume are two) and the model. In this project the harness also asks before the command runs (`references/project.md`). Wait for an explicit "yes". A "yes" covers that run only.

```
uv run python labs/<app-name>/app.py
```

With tracing on, check afterwards what the run left in LangSmith before repeating it, so nothing is duplicated; reading the traces (count, latency, tokens, links) is the ops-traces skill.

Check, in this order:

1. The receipt line: model calls and tokens are what you expected.
2. `runs/<timestamp>/` exists with `events.jsonl` and `transcript.md`. Open the transcript and read it: every tool result must appear as a new message in the next model call.
3. The searches the agent wrote are complete questions, and another `thread_id` does not know the first conversation.

If a check fails: look up the symptom in `references/gotchas.md`, fix only that, run the offline checks again and ask before the next paid run. If it cannot run (no key, no network), say so and leave the exact command.

## 3. Delivery

Answer with: the file paths, the command, the path of `transcript.md` with an invitation to read it call by call, the receipt (model calls, tokens), a three-row table with the tools, the thread and the checkpointer that were built, and the final blueprint. Suggest a single next step: the next piece the app needs (a database checkpointer for a service), or measuring it with the eval-experiments skill.
