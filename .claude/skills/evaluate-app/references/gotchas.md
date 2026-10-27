# Gotchas: symptom → cause → fix

Observed with `langsmith`, `openevals` and `claude-haiku-5-5` while evaluating a RAG app.

| Symptom | Cause | Fix |
|---|---|---|
| Judgements end as "Invalid format: 'score'" | The judge ran out of tokens while reasoning (`stop_reason="max_tokens"`) | A larger budget for the judge (2000) than for the answers (500) |
| Some judgements arrive without `score` although the call succeeded | `create_llm_as_judge` uses a tool without a schema guarantee | `with_structured_output(Judgement, method="json_schema")` |
| A judge failure lowers the average | The failure was scored 0 | Return `score=None` with "Invalid format"; averages ignore `None` |
| The judge approves answers that look like its own | The judge is the same model as the app | Calibrate against human labels and read the disagreements; consider a different judge model only with evidence |
| Setting `LANGSMITH_TRACING` or `LANGSMITH_PROJECT` with `os.environ` mid-run has no effect | `langsmith` reads them once and caches them | `tracing_context(enabled=True, project_name=...)` around the block |
| The experiment shows only the model call, not what was retrieved | The app and the retriever are not traced | `@traceable(name=...)` on the app and `@traceable(run_type="retriever")` on the retriever |
| One trace per judgement fills the budget | Evaluator tracing is on | `evaluate(..., disable_evaluator_tracing=True)`: one trace per answer, scores still saved |
| Calibration appears as 8 loose traces | Each judgement is a top-level call | Group them in `with trace("calibration", ...)` |
| Reading the project right after tracing says it does not exist | Traces upload in the background | `client.flush()` before reading |
| A dry run creates an empty project with a random name | `evaluate(upload_results=False)` with `LANGSMITH_API_KEY` set | Unset the key and mock `Client` in offline checks |
| Changing the references does not change the experiments | The dataset already existed and is reused | Use a new dataset name, or delete the old one with the person's approval |
| `citations_ok` fails on a correct answer | The answer has no citation: correctness and citations are different things | Expected; report both |
| `retrieval_hit` average looks higher than expected | Questions without an answer score `None` and are left out | Report the number of questions each average uses |
| Two configurations swap places between runs | Few questions and answers that vary between runs | Report the number of questions; use more questions and `num_repetitions` before deciding |
| Rate-limit errors with many people running at once | Too much concurrency | `max_concurrency=2` |
| The report is empty or misses the last examples | Read before the traces finished uploading | `client.flush()` before `report()` |
| A judge is built and fails with "unknown placeholders" | The rubric uses a name the field mapping does not fill | Use `{inputs}`, `{outputs}`, `{reference_outputs}`, `{context}`, or pass another `fields` mapping |
| `figures_match` fails on "0,5" against "0.5" | The decimal separator differs | Normalize separators in the evaluator for your locale |
| The sign test says p=1.0 although the means differ | The difference comes from questions only one experiment scored | Compare on paired questions; read the n of each mean |
