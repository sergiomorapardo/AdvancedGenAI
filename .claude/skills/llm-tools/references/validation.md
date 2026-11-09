# Check, run and deliver

## 1. Offline checks (no model calls)

Run them before asking for the paid run:

```
uv run python -c "import ast, pathlib; ast.parse(pathlib.Path('labs/<app-name>/app.py').read_text())"
uv run --locked ruff check labs/<app-name>
```

Then, in a short `uv run python` snippet that imports `app` without calling `main()`:

1. **Tools**: call each tool with `tool.invoke({...})` for a found case, a not-found case and an invalid argument. The invalid argument must raise a `ValidationError` before the function runs.
2. **Answer check**: call `check_answer` with a `ToolMessage` and an answer that uses its figure (`True`) and one that does not (`False`).
3. **MCP** (no model; the servers start as subprocesses): `await load_tools(...)` lists the prefixed names; run the agent with a fake model that calls one tool and check the `ToolMessage` holds the server's figure; with an ambiguous input, `state["__interrupt__"]` carries the server's question and the options, and resuming with one option returns only its rows.

None of these call the model or create traces (`tool.invoke` creates a trace only if LangSmith is on).

## 2. The paid run

Before running, tell the person exactly: the command, the number of model calls (an agent: 2 or more, depending on the question), the traces (0 with tracing off; otherwise 1 per top-level invoke) and the model. In this project the harness also asks before the command runs (`references/project.md`). Wait for an explicit "yes". A "yes" covers that run only.

```
uv run python labs/<app-name>/app.py
```

With tracing on, check afterwards what the run left in LangSmith before repeating it, so nothing is duplicated; reading the traces (count, latency, tokens, links) is the ops-traces skill.

Check, in this order:

1. The receipt line: model calls and tokens are what you expected.
2. `runs/<timestamp>/` exists with `events.jsonl` and `transcript.md`. Open the transcript and read it: every tool result must appear as a new message in the next model call.
3. The transcript shows the tool calls you expected, with sensible arguments.
4. The answer check passes: the figures in the answer come from the tool.

If a check fails: look up the symptom in `references/gotchas.md`, fix only that, run the offline checks again and ask before the next paid run. If it cannot run (no key, no network), say so and leave the exact command.

## 3. Delivery

Answer with: the file paths, the command, the path of `transcript.md` with an invitation to read it call by call, the receipt (model calls, tokens), a three-row table with the tools, the system prompt and the guardrails that were built, and the final blueprint. Suggest a single next step: the next piece the app needs (documents with llm-rag, memory with agentic-memory), or measuring it with the eval-experiments skill.
