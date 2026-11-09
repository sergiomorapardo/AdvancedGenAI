# Check, run and deliver

## 1. Offline checks (no model calls)

Run them before asking for the paid run:

```
uv run python -c "import ast, pathlib; ast.parse(pathlib.Path('labs/<app-name>/app.py').read_text())"
uv run --locked ruff check labs/<app-name>
```

Then, in a short `uv run python` snippet that imports `app` without calling `main()`:

1. **Template**: render each Jinja template with its `.example.json` and print the result. Remove one required field and confirm `StrictUndefined` raises `UndefinedError`.
2. **Schema**: `Schema.model_validate({...})` with a bad value fails and names the field.
3. **Prompt**: `PROMPT.format_messages(...)` and read the messages the model will receive: the user's text is its own human message.

None of these call the model or create traces.

## 2. The paid run

Before running, tell the person exactly: the command, the number of model calls (a chain: 1 per run), the traces (0 with tracing off; otherwise 1 per top-level invoke) and the model. In this project the harness also asks before the command runs (`references/project.md`). Wait for an explicit "yes". A "yes" covers that run only.

```
uv run python labs/<app-name>/app.py
```

With tracing on, check afterwards what the run left in LangSmith before repeating it, so nothing is duplicated; reading the traces (count, latency, tokens, links) is the ops-traces skill.

Check, in this order:

1. The receipt line: model calls and tokens are what you expected.
2. `runs/<timestamp>/` exists with `events.jsonl` and `transcript.md`. Open the transcript and read it.
3. The fields of the output agree with the input: no field invented, every missing one listed.

If a check fails: look up the symptom in `references/gotchas.md`, fix only that, run the offline checks again and ask before the next paid run. If it cannot run (no key, no network), say so and leave the exact command.

## 3. Delivery

Answer with: the file paths, the command, the path of `transcript.md` with an invitation to read it call by call, the receipt (model calls, tokens), a three-row table with the prompt, the input and the output schema that were built, and the final blueprint. Suggest a single next step: the next piece the app needs (a tool with llm-tools, documents with llm-rag), or measuring it with the eval-experiments skill.
