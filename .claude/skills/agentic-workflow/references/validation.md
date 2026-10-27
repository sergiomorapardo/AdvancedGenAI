# Check, run and deliver

## 1. Offline checks (no model calls)

Run them before asking for the paid run:

```
uv run python -c "import ast, pathlib; ast.parse(pathlib.Path('labs/<app-name>/app.py').read_text())"
uv run --locked ruff check labs/<app-name>
```

Then, in a short `uv run python` snippet that imports `app` without calling `main()`:

1. **Template**: render each Jinja template with its `.example.json` and print the result. Remove one required field and confirm `StrictUndefined` raises `UndefinedError`.
2. **Tools**: call each tool with `tool.invoke({...})` for a found case, a not-found case and an invalid argument. The invalid argument must raise a `ValidationError` before the function runs.
3. **Schema**: `Schema.model_validate({...})` with a bad value fails and names the field.
4. **Prompt**: `PROMPT.format_messages(...)` and read the messages the model will receive.
5. **RAG** (no model, embeddings are local): print the pages and fragments with their metadata; for two or three questions with a known answer, check that the expected file and page appear in the top `k` of `similarity_search`; call `check_citations` with a fake answer that cites a retrieved page (`True`) and one that cites another page (`False`). Measuring retrieval over a whole question set, and comparing configurations, belongs to the evaluate-app skill.
6. **Conversation** (no model): show that the follow-up alone retrieves the wrong pages with `similarity_search`; run the chain or the agent with `GenericFakeChatModel` to check that the retriever receives the rewrite, and that two `thread_id`s keep only their own messages (`get_state`).

7. **MCP** (no model; the servers start as subprocesses): `await load_tools(...)` lists the prefixed names; run the agent with a fake model that calls one tool and check the `ToolMessage` holds the server's figure; with an ambiguous input, `state["__interrupt__"]` carries the server's question and the options, and resuming with one option returns only its rows.

None of these call the model or create traces (`tool.invoke` creates a trace only if LangSmith is on).

## 2. The paid run

Before running, tell the person exactly: the command, the number of model calls (a chain: 1 per run; an agent: 2 or more, depending on the question), the traces (0 with tracing off; otherwise 1 per top-level invoke) and the model. In this project the harness also asks before the command runs (`references/project.md`). Wait for an explicit "yes". A "yes" covers that run only.

```
uv run python labs/<app-name>/app.py
```

Check, in this order:

1. The receipt line: model calls and tokens are what you expected.
2. For an agent, the transcript shows the tool calls you expected, with sensible arguments.
3. `runs/<timestamp>/` exists with `events.jsonl` and `transcript.md`. Open the transcript and read it: every tool result must appear as a new message in the next model call.
4. The answer check passes: the figures in the answer come from the tool or the input; with RAG, `check_citations` is `True` and a question without an answer says so.

If a check fails: look up the symptom in `references/gotchas.md`, fix only that, run the offline checks again and ask before the next paid run. If it cannot run (no key, no network), say so and leave the exact command.

## 3. Delivery

Answer with: the file paths, the command, the path of `transcript.md` with an invitation to read it call by call, the receipt (model calls, tokens), a three-row table with the prompt, the tools or documents and the guardrails that were built, and the final blueprint. Suggest a single next step: the next piece the app needs, or measuring it with the evaluate-app skill.
