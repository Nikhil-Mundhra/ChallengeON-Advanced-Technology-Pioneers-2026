# Agent

Entry point for the Abu Dhabi Tourism Digital Twin (ChallengeON ATP 2026, DCT challenge). Pick the route for the task, read that file, follow its `## Calls`.

## Route
- Python code in `src/`: setup, layering, data access, features, tests → `agents/code/python.md`
- web app in `web/`: engine, components, copy, styling → `agents/code/web.md`
- code comments in any language → `agents/code/comments.md`
- guest model: components, specs, fitting, inputs, events, nowcast and planning equations → `agents/model/guest-model.md`
- comparing, validating or scoring models; shipping a component; reporting a result → `agents/model/evaluation.md`
- lake artifacts, raw workbooks, submission files, generated output, the web bundle → `agents/data/artifacts.md`
- presentation deck in `meta/deck/` → `agents/deck.md`
- writing or changing any .md → `agents/docs/writing.md`
- syncing docs after commits → `agents/docs/sync-docs.md`
- syncing routes and guides after commits → `agents/docs/sync-agent.md`
- judging the project against the challenge brief → `agents/meta/review.md`
- facts: data, architecture, model, evidence, results, commands → `docs/index.md`
- data-audit tool in `src/audit_agent/` → `src/audit_agent/README.md`
- a task a skill covers → `.agents/skills/<name>/SKILL.md`; skills: `data-lake-and-zone-architecture`, `data-quality-and-contract-testing`, `data-reconciliation-and-financial-controls`, `dct-tourism-hackathon-reviewer`, `duckdb-local-analytics-and-dev`, `feature-store-and-ml-data-pipelines`, `file-and-partner-feed-ingestion`, `glassmorphism-ui`, `master-data-and-entity-resolution`, `notebook-to-production-hardening`, `python-data-engineering-and-pipeline-packaging`, `semantic-layer-and-metric-governance`, `warehouse-and-schema-design`

## Rules
- commit: `make test` green; the message names no tool or co-author; no attribution trailers.
- licence: the DCT competition data is used only within the competition; raw workbooks and raw arrivals never leave the machine (`agents/data/artifacts.md`).
- change: one file, one responsibility; update the owning map or doc in the same change.
- metrics: a metric or behaviour change ships as its own change and is reported; never silently.
- refactor: prove unchanged outputs: rebuild into a scratch dir and compare with the committed artifacts.
- delete/rename: grep the symbol or path, remove its references first, re-grep returns nothing.
- records: dated records keep their historical paths: `meta/audits/data_issues/`, `meta/research/real_world_validation/*.md`, evidence strings in `scripts/direct_audit_runner.py`.
- conflict: code is the source; a guide or doc that disagrees with it is corrected, never followed.
- docs: kebab-case `.md` names; root standards (`AGENTS.md`, `README.md`, `CLAUDE.md`) stay UPPER.
- entry: `CLAUDE.md` is a byte copy of `AGENTS.md`; edit `AGENTS.md`, then `cp AGENTS.md CLAUDE.md`.
- icons: no emoji in UI, copy, code, commit messages or docs.

## File structure

```
.agents/skills/ : skill folders, one `SKILL.md` each
.opencode/agents/audit-escalation.md : read-only escalation agent of the data-issues audit (`src/audit_agent/escalation.py`)
Makefile : pipeline, test, web and server targets; `make docs-lint`
README.md : project summary for visitors: what it does, install, run, links into `docs/`
docs/ : facts: data, architecture, model, evidence, results, user guide
lake/ : curated tables and model artifacts
meta/ : deck source, research outputs, audit inputs and dated records
pyproject.toml : package metadata, dependencies and extras
scripts/ : research, audit and maintenance scripts; `scripts/docs_lint.py`
src/ : Python packages `tourism_twin`, `app`, `audit_agent`
tests/ : Python tests, one folder per package
web/ : static React site and its TypeScript engine
```
