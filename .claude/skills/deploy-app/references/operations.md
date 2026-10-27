# Operations: what to watch once people use it

## Before release

- **Evaluate the app**, not the API: a dataset with references, code evaluators and, if needed, a calibrated judge (evaluate-app). Keep the experiment's link and numbers with the release.
- **Cost of a typical turn**: model calls and tokens from the turn log × the model's price. Report it per turn and per conversation of the expected length; the history grows on every turn of a thread.
- **Limits**: maximum message length, maximum turns per thread if the history must stay bounded, and a timeout on the model.

## While it runs

| Signal | Where it comes from | What it tells |
|---|---|---|
| Model calls and tokens per turn | The turn log (`turn_usage`) | Cost, and loops in an agent (more calls than expected) |
| Latency per turn | The access log or a timer around `invoke` | The slowest step; streaming hides it from the person, not from the bill |
| Errors and timeouts | The API log | Provider limits, network, a tool that raises |
| Traces | LangSmith, in a project for this environment | Which steps ran, with what inputs, when something looks wrong |
| Quality | Periodic experiments on the same dataset (evaluate-app) | Regressions after a prompt, model or dependency change |

Traces are optional and spend a monthly budget: turn them on for a period or a sample, not forever by default.

## When something changes

A new prompt, model, tool or dependency is a new version: run the offline tests, the startup check and the evaluation before deploying it, and compare with the previous experiment. Dependency updates go through their own PRs with the same checks.

## Security

- **Exposure**: the examples have no authentication and no ownership of chats: anyone who reaches the port can read any thread whose id they guess. Keep them on `127.0.0.1`; before any other exposure add authentication, map users to their own threads and add rate limits.
- **Secrets**: keys and `DB_URI` live in `.env` (or a secret manager in production), never in code, images, logs or responses.
- **Tools**: read only unless an action has human approval (agent-patterns); the API never adds tools the graph did not have.
- **Data**: synthetic or anonymized in the course; never log message contents with personal data.
- **Database**: demo credentials and a loopback port; back up the volume before any migration; deleting it deletes conversations.
