# Sync docs

last synced: 865e50d

## Calls
- `agents/docs/writing.md` : doc format; the rules every changed doc must still meet
- `agents/code/comments.md` : comment rules checked on changed code

## Rules
- runner: a cold subagent runs this guide; the main session reviews its edits and commits docs separately from code.
- owning map: the guide or index whose map holds the path's prefix; a new doc gets a line in its folder's `index.md`; a new guide gets a `## Route` or `## Calls` line (`agents/docs/sync-agent.md`).
- sections: keep each file's existing sections; add none.
- report only: contradicted rules, writing violations and comment violations are reported, not fixed.
- scope: files changed in the range only; skip `web/public/data/`, `lake/curated/`, `meta/research/`, `meta/audits/`, lock files and build output.

## Workflow
1. Unchecked changes: `git log --stat --reverse <last synced>..HEAD` plus `git status --short`. A `last synced:` that is not an ancestor of HEAD (rewritten history): use the HEAD commit with the same subject, else the whole history, and say which in the report.
2. Read each added, renamed or modified file; add, delete, re-path or rewrite its map line (rewrite only if the file's job changed).
3. Docs that describe a changed file: grep `docs/` for its path, basename and new exported names; correct each stale statement and add each missing item. A changed file that adds an invariant no doc states: add it as a fact to the doc that owns the file's area. A changed result artifact (`lake/curated/evaluation_results.json`, `output/validation_summary.json`, `output/outlook.json`): update `docs/results/*` from the artifact only, never from memory or another doc.
4. Every `## Rules` line in `AGENTS.md` or `agents/` that a changed file now contradicts: report it with that file.
5. Every doc or guide changed in the range: check it against `agents/docs/writing.md` (including its `language` rule); every changed code line: check its comments against `agents/code/comments.md`. Report directives or reasoning in docs, a fact with two owners, a result number outside `docs/results/` or `docs/evidence/`, a doc cited by section number, and any real host, username or key.
6. `make docs-lint`, report, set `last synced:` to `git rev-parse --short HEAD`.

## Report

```
rule <guide>:<line> : contradicted by <path>
writing <path>:<line> : <violation>
comment <path>:<line> : <violation>
lint <check> <path> : <message>
```

- Empty report: `no findings`.
