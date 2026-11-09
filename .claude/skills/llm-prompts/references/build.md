# Build: pieces, files and rules

## Contents

- Which piece to use
- Files to generate
- Rules that are not negotiable
- Project specifics

## Which piece to use

- **Chain** (`chain.py`): `PROMPT | model.with_structured_output(Schema)`. Use it when the steps are fixed.
- **Jinja template** (`jinja_prompt.py`): `prompts/<name>.jinja` loaded from the script's folder with `FileSystemLoader(Path(__file__).resolve().parent / "prompts")` and `StrictUndefined`. Render the system prompt with Jinja; pass the user message as data in a separate human message, never through Jinja. Next to each template, write `<name>.example.json` with a realistic context: the repo's Jinja hook renders it with `StrictUndefined` after every edit.
- **Structured output**: a Pydantic model with a docstring and a `Field(description=...)` per field. Optional fields are `X | None`. Validate the shape with the schema and the content with a check against the input.
- **Run log** (`run_log.py`): copy it as is next to the app and pass `config={"callbacks": [run_log]}` on the top-level `invoke`. Print `run_log.receipt()` at the end.

## Files to generate

Copy `assets/app.py`, fill the `TODO` marks and delete what the blueprint does not use. Output structure, in a new folder named after the app:

```
labs/<app-name>/
  README.md                 # problem, success criteria, how to run, cost of one run
  app.py                    # from assets/app.py
  project.py                # copied as is from references/examples/project.py
  run_log.py                # copied as is from references/examples/run_log.py
  prompts/<name>.jinja      # only with a Jinja prompt
  prompts/<name>.example.json
  .gitignore                # runs/
  runs/<timestamp>/         # events.jsonl + transcript.md, one folder per run
```

The `README.md` states the problem in one sentence, two or three success criteria the person can check (for example "lists the missing fields of an incomplete dispute ticket"), the command, and the cost of one run in model calls and traces.

## Rules that are not negotiable

1. **Model**: `build_model(max_tokens=...)` from `project.py`, nothing else creates a chat model. Its settings and why are in `references/project.md`. Do not switch to a bigger model on your own.
2. **Credentials**: `build_model()` loads them the way the project decides. Never write a key, never print `.env`.
3. **Run log always**; never filter events before saving them and never remove it to "simplify".
4. **Tracing off by default.** With LangSmith, every top-level `invoke`, `batch` or `stream` is one trace, including `ChatPromptTemplate.invoke`; fill templates with `format_messages` when the trace is not needed.
5. **Synthetic data** in the code: a realistic input with one or two traps (a missing field, an empty list). Real data only if it is authorized and anonymized.
6. **Names in English** for files, functions, classes and variables.
7. **Keep it simple**: the smallest code that meets the goal, no helpers the blueprint does not need.

## Project specifics

Where apps live, which packages are allowed, the branch convention, the repository tools and the hooks that check what you write are in `references/project.md`. Read it before generating files.
