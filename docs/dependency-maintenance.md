# Dependency maintenance

Version updates, security advisories and upstream retirement are separate signals.
Dependabot proposes updates; `pip-audit` checks known vulnerabilities in the lock;
upstream release notes and deprecation notices guide replacement decisions.
Neither an old version nor a quiet release history alone proves abandonment.

## Review cadence

- Weekly: review Dependabot PRs and the CI `quality-reports` artifact. `uv tree
  --locked --outdated --depth 1` reports updates without changing the lock.
- For each dependency PR: inspect release notes and breaking changes, run tests,
  LangGraph startup and build checks, then merge individually with squash.
- Monthly and before course releases: review upstream maintenance status for
  direct dependencies and APIs used in agents/notebooks. Record official sunset
  announcements, affected imports, alternatives and a migration plan here.
- For security findings: confirm affected functionality and fixed versions.
  Remediate in focused PRs; where no fix exists, assess exposure and replacement.
  Do not suppress all findings or update unrelated dependencies indiscriminately.

Dependabot runs Mondays at 09:00 America/Bogota for the `uv` and `github-actions`
ecosystems. Related LangChain/LangGraph patch/minor updates form one group;
quality-tool patch/minor updates form another. Major updates remain separate.
See the [official Dependabot options](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference).
The bot's generated branches follow Dependabot conventions; the `feature/` rule
in AGENTS.md applies to branches we create ourselves.

## Sunset review: 2026-10-02

| Dependency/API | Evidence and affected code | Proposed follow-up |
| --- | --- | --- |
| `langchain-community` | The maintainers announced an immediate sunset and archived the repository. Used by document loaders in `src/agents/rag.py`, `src/agents/support/nodes/conversation/tools.py` and notebooks L2–L5; L2/L3 also use the FAISS wrapper. | In a separate migration PR, evaluate maintained standalone integrations. For PDF loading, evaluate the existing `pypdf` dependency with LangChain `Document` objects. Verify loader metadata, PDF behavior, FAISS retrieval and lesson examples before removing the package. No replacement has been selected or applied yet. |
| `langgraph.graph.MessageGraph` | Deprecated upstream; imported but unused in `src/agents/simple.py`. That file already constructs `StateGraph`. | Remove the unused import during cleaning. No graph migration is needed for this import. |

Sources: [LangChain sunset announcement](https://github.com/langchain-ai/langchain-community/issues/674),
[LangGraph graph API](https://reference.langchain.com/python/langgraph/graph).
This is a targeted review, not a claim that every dependency has been assessed
for support status. Retain FAISS and Chroma until their actual usage and
replacement behavior have been reviewed.

## Initial security and quality baseline

Local audit on 2026-10-02 reported 11 vulnerability entries across five packages;
one Chroma advisory appeared twice. The audit covers the exported lock for the
current platform, including runtime, dev and quality groups. CI audits Linux;
findings can change as advisories and platform-specific dependencies change.

| Locked package | Reported advisory IDs | Fixed versions reported by the audit |
| --- | --- | --- |
| `chromadb==1.5.9` | `PYSEC-2026-311`, `PYSEC-2026-3813`, `PYSEC-2026-3814`, `PYSEC-2026-3815` | None reported |
| `jupyterlab==4.6.3` | `PYSEC-2026-4055`, `PYSEC-2026-4056`, `PYSEC-2026-4057` | 4.5.11 or 4.6.4; evaluate 4.6.4 for the installed series |
| `notebook==7.6.2` | `PYSEC-2026-4112` | 7.6.3 |
| `oauthlib==3.3.1` | `PYSEC-2026-4114` | 4.0.0 (major update; review compatibility) |
| `pyjwt==2.14.0` | `PYSEC-2026-4141` | 2.15.0 |

This table records tool output, not a determination of exploitability or complete
security coverage. No runtime dependency was upgraded in this housekeeping PR.
The generated audit artifact is the current source of findings, rather than
this historical table. `pip-audit` detects known dependency vulnerabilities;
Bandit checks Python patterns, and private-key hooks do not detect every secret.
See [pip-audit](https://github.com/pypa/pip-audit) for scope and limitations.

The initial code reports contain 17 full-lint findings, 11 files requiring
formatting and four mypy assignment errors in `simple.py`/`contact.py`. Fatal
Ruff checks and medium/high Bandit checks pass. Notebooks are syntax-checked
without executing their API calls; mypy/Bandit/full-format reports target Python
source, tests (Ruff) and CI scripts.

Reproduce the security report without installing every runtime dependency:

```sh
uv sync --locked --only-group quality
uv export --locked --all-groups --no-emit-project --format requirements-txt --output-file /tmp/advancedgenai-audit-requirements.txt > /dev/null
uv run --no-sync pip-audit --require-hashes --no-deps --disable-pip --strict -r /tmp/advancedgenai-audit-requirements.txt --format markdown
```

## Transition to blocking checks

The user chose visible advisory reports while existing findings are corrected.
The exception is temporary and applies to full lint, formatting, types and the
dependency audit. Tests, startup, read-only hooks, medium/high Bandit and build
steps retain failing exit statuses.

After the cleaning and security remediation PRs:

1. Enable full Ruff lint in `pyproject.toml` and make format/mypy hooks automatic.
2. Remove `continue-on-error` from resolved lint, format, types and audit steps.
3. Add the `quality` job to required GitHub checks after confirming it passes.
4. Revisit unavailable fixes individually with documented exposure, owner and
   review date if an exception remains necessary. Do not silently ignore them.

Enable the audit gate after its findings are resolved or explicit individual
exceptions have been reviewed. A failing audit can also indicate a collection or
network error; inspect the artifact/logs rather than assuming every failure is
a vulnerability.
