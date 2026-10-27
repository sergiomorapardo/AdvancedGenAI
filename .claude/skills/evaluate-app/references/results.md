# Download the results and interpret them

`examples/results.py` reads the experiments back from LangSmith and writes `results/<timestamp>/` next to the script that runs it:

- `traces.jsonl`: every run of every trace (the app, the retriever, the model call) with inputs, outputs, errors and seconds. It stays on the machine: it can contain model answers, so it is in `.gitignore`.
- `rows.json`: one row per example and experiment, with answer, reference, scores, judge comments, tokens and seconds per step.
- `report.md`: the tables below, printed as well.

`evaluation.py` calls it at the end of every run. For experiments that already exist, pass their names and the number of evaluators: `uv run python <skill>/references/examples/results.py EXP_A EXP_B --scores 5`. LangSmith stores feedback late: with `--scores` the script waits until every row has its scores, so the report never compares unscored rows. Reading creates no traces and calls no model; it does use the LangSmith API, so `LANGSMITH_API_KEY` must be set. Call `client.flush()` first when the experiments were created in the same process.

## What the report contains

| Section | What it answers |
|---|---|
| Summary | Mean of each evaluator with the **n** it averages (rows with a score), median and max latency, cost of the answers, errors |
| B against A, question by question | For each evaluator, on the questions both scored: where B is better, worse or equal, and the two-sided sign test p-value |
| Where the answers fail | For each experiment: ok, retrieval failures (the expected page never arrived), generation failures (it arrived and the answer is still wrong), other |
| Questions to read | Every question where an experiment failed or where they differ, with the reference, each answer and the judge's comment of each failed evaluator |
| Signals for the conclusion | Rules the conclusion must respect: incomplete experiments, judge format failures, small samples, differences not demonstrated |

The diagnosis uses the keys `retrieval_hit` and `correctness`; with other evaluators, pass their keys to `diagnose`.

## Interpret: three kinds of statement

Write the conclusion yourself from the report, and label each statement:

1. **Supported by the data**: a difference that holds on enough paired questions (sign test p < 0.05) with no errors or unread format failures. Example: "B fails 0 of 30 retrieval questions where A fails 6 (p=0.03)".
2. **Reasonable hypothesis**: a direction the data suggests but does not demonstrate, with what would confirm it. Example: "B is better in 2 and worse in 0 of 5 questions (p=0.50): likely better on figures; confirm with the 16 questions and 3 repetitions".
3. **Not supported**: anything the report cannot say. Example: "B is 20 points better" with 5 questions, a judge that was not calibrated, or experiments with errors.

Then:

- **Read the cases before the averages.** Open the "Questions to read" section and the traces of two of them. A mean hides which questions changed and why.
- **Separate retrieval from generation.** A retrieval failure is fixed in the index or the retriever; a generation failure in the prompt or the model. Do not propose a prompt change for a page that never arrived.
- **Trust the judge only as far as its calibration.** If a disagreement in calibration matches a failure in the experiments, say so.
- **Weigh quality against latency and cost**, with the figures of the summary. A tie in quality with lower cost is a decision too.
- **Variability.** Model answers change between runs; one run per configuration cannot separate a real difference from noise. Propose `num_repetitions` before a decision that matters.

## Deliver

The summary table, the comparison table, two or three questions where the configurations differ (answer of each and why it failed), the conclusion with its three kinds of statement, and one next step: more questions, repetitions, or the one change to test next. Give the path of `report.md` and the LangSmith links printed by `evaluate`.
