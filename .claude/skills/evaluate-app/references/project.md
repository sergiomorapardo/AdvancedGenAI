# This project: AdvancedGenAI course repository

Everything that ties the skill to this repository lives here and in `examples/project.py`. To reuse the skill elsewhere, rewrite these two files; the rest of the skill stays as is.

## Model and credentials

- `examples/project.py` builds `ChatAnthropic(model="claude-haiku-5-5", thinking={"type": "disabled"}, timeout=60, max_retries=2)` with `max_tokens=500` for answers; the judge raises it to 2000. No `temperature`: Haiku 5.5 rejects it. The judge uses the same model unless the person decides otherwise with evidence.
- Credentials: `load_dotenv(find_dotenv())` reads the repository `.env`. `LANGSMITH_API_KEY` must be there; `LANGSMITH_TRACING` can stay `false`. Never write a key, never print `.env`.
- `PRICE_PER_MILLION` in `project.py` is the price used for the cost column; check it against the current price list before reporting cost.

## LangSmith budget and naming

- The free tier has a monthly trace limit. Count and report traces before every run and wait for approval; deleting experiments or datasets needs explicit approval.
- One project per app or notebook (the course uses `advancedgenai-<notebook>`), a `PARTICIPANT` name as tag, metadata and experiment prefix, so that everyone filters their own runs in a shared workspace.
- Print links to the project, the dataset, each experiment and the comparison view, and read them before calling the evaluation done.

## Where things live

- Sample corpus and evaluation set of the example: the synthetic ACME policies in `datasets/acme_*.pdf`, `datasets/acme_questions.csv` (22 questions with expected file, page and reference; three have no answer in the documents) and `datasets/acme_review_set.csv` (8 answers labeled by a person).
- An app's evaluation lives next to it: `labs/<app-name>/evaluate.py`, `evaluators.py`, `results.py` and `eval/`, in its feature branch; see `AGENTS.md`.
- Downloaded results go to `results/<timestamp>/` next to the script; `.gitignore` excludes them (`labs/*/results/` and the example's folder) because they can contain model answers.
- Install nothing outside uv; `openevals` and `langsmith` are already in `pyproject.toml`.

## Controls the repository enforces

- Hook `.claude/hooks/check_app.py`: after every edit of a Python file under `labs/`, checks syntax, `ruff`, no `temperature=` and no literal API key.
- Permissions in `.claude/settings.json` ask before running `labs/` and the skill examples.
- Offline tests of the example: `uv run python -m unittest tests.test_evaluate_app`.

## The course behind it

Distilled from `notebooks/L11-RAGEvaluation.ipynb` (week 6), which compares the cosine and RRF retrievers with 38 calls and 11 traces on five questions. The script compares `k=3` with `k=5` to stay short, and stops if the judge agrees with the person less than 75 %. LangSmith stores feedback late and returns boolean scores as 1.0/0.0, so `results.py` waits for every score and compares with `None`. Agent and graph evaluation (`references/agents.md`) follows the paths of weeks 3 to 11: tool calls (L04, L13), routes (L18), plans (L21), approvals (L20) and loops (L22). Production monitoring belongs to the deploy-app skill.
