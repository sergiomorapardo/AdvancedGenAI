# Build the evaluators

Write one evaluator per criterion a person can state in one sentence ("every figure of the reference appears in the answer"). Start with code; add a judge only for what code cannot see. Copy the shapes from `examples/evaluators.py`.

## Contents

- The contract
- Code or judge
- Code evaluators
- Judges from a rubric
- Calibrate before trusting
- Checks before any paid run

## The contract

- A function whose parameters are named `inputs`, `outputs` and/or `reference_outputs`: LangSmith passes them by name, so ask only for what you use.
- It returns `{"key": ..., "score": ..., "comment": ...}`. `score` is `True`/`False` or a number; `None` when it does not apply or the judge failed. `None` never counts as 0.
- The `key` is the column name in LangSmith and in the report: short, `snake_case`, the same across experiments.
- The app under test must return everything the evaluators read (answer, retrieved sources, context, tokens). If an evaluator needs a field the app does not return, change the app, not the evaluator.

## Code or judge

Ask the person, one criterion at a time, with AskUserQuestion: "Can a rule decide it?"

| Criterion | Evaluator | Example in `evaluators.py` |
|---|---|---|
| The expected document or page was retrieved | Code | `retrieval_hit` |
| Every citation points to something retrieved | Code | `citations_ok` |
| The figures of the reference are in the answer | Code | `figures_match` |
| An exact field, a format, a JSON schema, a length, a forbidden word | Code: compare, regex or `model_validate` | write it like the three above |
| It says "not in the documents" when it should | Code if the wording is fixed; judge otherwise | — |
| The answer means the same as the reference | Judge with the reference | `make_judge` + correctness rubric |
| Every claim is in the retrieved fragments | Judge with the context, no reference needed | `make_judge` + groundedness rubric |
| Tone, completeness, usefulness for the person who asked | Judge, only with a written rubric | `make_judge` |

A code evaluator that encodes the rule beats a judge that reads it: it costs nothing, never changes its mind and can be tested.

## Code evaluators

1. Write the rule in one sentence in the docstring.
2. Return `None` with a comment when the rule does not apply (a question without an answer has no page to retrieve).
3. Put in `comment` what failed (`Missing: ['6']`), so the report shows why without opening the trace.
4. Test it without the model: one output that passes, one that fails and one where it does not apply.

## Judges from a rubric

`make_judge(judge, key, rubric, fields)` turns a rubric into an evaluator. `judge` is `build_judge_model(model)`: structured output with `method="json_schema"` and a larger token budget, because the judge reasons before scoring.

Write the rubric:

1. Start from the closest OpenEvals prompt (`from openevals.prompts import ...`): `CORRECTNESS_PROMPT` (`{inputs}`, `{outputs}`, `{reference_outputs}`), `RAG_GROUNDEDNESS_PROMPT` (`{context}`, `{outputs}`), `RAG_RETRIEVAL_RELEVANCE_PROMPT` (`{inputs}`, `{context}`), `RAG_HELPFULNESS_PROMPT`, `HALLUCINATION_PROMPT`, `CONCISENESS_PROMPT`, `TOOL_SELECTION_PROMPT`, `TASK_COMPLETION_PROMPT`. Print it before adapting it.
2. Translate it to the language of the answers and of the domain.
3. Say what passes and what fails, with the errors that matter in this process (a wrong figure, a missing deadline, the rule of another product).
4. Say what it must **not** judge (style, length, citations when another evaluator checks them).
5. Ask for the reasoning before the score, and a binary score: two people agree more on pass/fail than on a 1–10 scale.
6. Use only the placeholders the evaluator can fill. `RAG_FIELDS` maps `{inputs}`, `{outputs}`, `{reference_outputs}` and `{context}` to a RAG app; pass another mapping for another app. An unknown placeholder raises an error when the judge is built, before any call.

Keep the rubrics in a file next to the evaluation (`prompts/judges.py` or the evaluation script), versioned like code: a rubric change is a new evaluator, so experiments before and after it are not comparable.

## Calibrate before trusting

`calibrate(evaluator, labeled)` compares the evaluator with a person on fixed answers:

- At least 8 answers, labeled by someone who knows the process: half correct (one paraphrased, one without citations) and half with the typical errors of the process.
- The answers are fixed in a file, not generated in each run, so the calibration is repeatable.
- Read every disagreement. If the judge fails on a type of error, change the rubric and calibrate again. Never drop the hard cases to raise the agreement.
- The example stops before the experiments when agreement is below `MIN_AGREEMENT`. That is a control in code, not a suggestion.
- High agreement on 8 answers is necessary, not sufficient: add labeled answers as the dataset grows.

## Checks before any paid run

- Each code evaluator: pass, fail and does-not-apply, without the model.
- Each judge: build it (placeholders are checked), format its rubric with one example and read it as the judge will; with a fake judge, check that a failure returns `score=None`.
- The calibration file: every row has an answer, a label and a note.
