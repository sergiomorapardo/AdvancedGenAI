# Check and run

## 1. Offline checks (no model, no LangSmith)

Unset `LANGSMITH_API_KEY` for these checks: with the key, even `evaluate(upload_results=False)` creates an empty project.

1. **Data**: every question has a reference; the expected file and page exist in the corpus; questions without an answer have an empty source.
2. **Evaluators**: the checks in `references/evaluators.md` (code evaluators pass/fail/does-not-apply; judges built, rubric read, fake failure is `None`).
3. **App under test**: run it with a fake chat model and check that it returns everything the evaluators read (answer, context, sources, tokens).
4. **Rubrics**: format each judge prompt with one example and read it as the judge will.
5. **Report**: feed `render_report` fake rows with a `None` score and a failed run; neither may count as 0, and the signals must name them.

## 2. The paid run

Tell the person: the command, the calibration calls, the experiment calls per configuration, the traces and the experiments it leaves, and whether earlier experiments with the same prefix exist (they would stay as duplicates). Wait for an explicit "yes"; it covers that run only.

Run the calibration first and read it before the experiments. If the judge disagrees with the person on a type of error, adjust the rubric and calibrate again; do not run the experiments with a judge you do not trust.

## 3. Results and delivery

When the run ends, `report()` downloads the experiments and writes the report. Read it and conclude as `references/results.md` says.
