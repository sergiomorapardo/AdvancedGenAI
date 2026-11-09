# Check, run and deliver

## 1. Offline checks (no model calls)

Run them before asking for the paid run:

```
uv run python -c "import ast, pathlib; ast.parse(pathlib.Path('labs/<app-name>/app.py').read_text())"
uv run --locked ruff check labs/<app-name>
```

Then, in a short `uv run python` snippet that imports `app` without calling `main()`:

1. **RAG** (no model, embeddings are local): print the pages and fragments with their metadata; for two or three questions with a known answer, check that the expected file and page appear in the top `k` of `similarity_search`; call `check_citations` with a fake answer that cites a retrieved page (`True`) and one that cites another page (`False`). Measuring retrieval over a whole question set, and comparing configurations, belongs to the eval-experiments skill.
2. **Conversation** (no model): show that the follow-up alone retrieves the wrong pages with `similarity_search`, and run the chain with `GenericFakeChatModel` to check that the retriever receives the rewrite.

None of these call the model or create traces.

## 2. The paid run

Before running, tell the person exactly: the command, the number of model calls (1 per question; 2 per follow-up with the rewrite; 1 more with multi-query), the traces (0 with tracing off; otherwise 1 per top-level invoke) and the model. In this project the harness also asks before the command runs (`references/project.md`). Wait for an explicit "yes". A "yes" covers that run only.

```
uv run python labs/<app-name>/app.py
```

With tracing on, check afterwards what the run left in LangSmith before repeating it, so nothing is duplicated; reading the traces (count, latency, tokens, links) is the ops-traces skill.

Check, in this order:

1. The receipt line: model calls and tokens are what you expected.
2. `runs/<timestamp>/` exists with `events.jsonl` and `transcript.md`. Open the transcript and read it.
3. `check_citations` is `True`, and a question without an answer says it is not in the documents.

If a check fails: look up the symptom in `references/gotchas.md`, fix only that, run the offline checks again and ask before the next paid run. If it cannot run (no key, no network), say so and leave the exact command.

## 3. Delivery

Answer with: the file paths, the command, the path of `transcript.md` with an invitation to read it call by call, the receipt (model calls, tokens), a three-row table with the documents, the index and the guardrails that were built, and the final blueprint. Suggest a single next step: the next piece the app needs (memory with agentic-memory, a tool with llm-tools), or measuring it with the eval-experiments skill.
