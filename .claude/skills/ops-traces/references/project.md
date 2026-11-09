# This project: the AdvancedGenAI course repository

Everything that ties the skill to this repository lives here and in `examples/project.py`. To reuse the skill elsewhere, rewrite these two files; the rest of the skill stays as is.

## Credentials and price

- `configure()` in `examples/project.py` loads the repository `.env` with `load_dotenv(find_dotenv())`. Reading needs `LANGSMITH_API_KEY`; never print `.env` or the key.
- `PRICE_PER_MILLION` holds the price of `claude-haiku-5-5` used across the course (US$0.10 input and US$0.50 output per million tokens). Check the current price before reporting a cost.

## How projects are named here

- Notebooks that trace use one project per notebook: `advancedgenai-lNN` (for example `advancedgenai-l11` for the RAG evaluation of week 6). The project name is printed in the notebook's setup cell.
- Without `LANGSMITH_PROJECT` or a `project_name`, LangSmith writes to the project called `default`; L03 sets `LANGSMITH_PROJECT=advancedgenai`. A trace in either one ran without its notebook's project: find the call before the next traced run.
- Experiments of a dataset are projects too, but they are read and compared with the eval-experiments skill.

## Budget and deletions

- LangSmith's free tier has a monthly trace limit. Reading does not count against it; every new traced run does. Before a traced run is repeated, read what the previous one left and say whether the new one would duplicate it.
- Deleting runs by id (`POST /api/v1/runs/delete`) is queued and can take hours; `client.delete_project` is immediate and removes every trace of the project. Both need the person's explicit "yes" for that exact deletion, after listing what will be deleted.

## Where results go

`traces.py` writes `results/<timestamp>/` next to itself; `.gitignore` excludes it because `runs.jsonl` holds model inputs and outputs. Offline tests: `uv run python -m pytest tests/test_ops_traces.py tests/test_skills.py`.
