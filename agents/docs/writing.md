# Writing docs

## Calls
- `scripts/docs_lint.py` : the checks `make docs-lint` runs

## Rules
- role: guides (`AGENTS.md` and `agents/`) hold directives; docs (`docs/`) hold facts.
- ownership: one fact, one owner; grep for it before writing; elsewhere link.
- edges: guides → docs → docs; never docs → guides.
- axes: each rule has one owner; a rule line starts with its topic.
- guide content: directives only; never restate what the code or the file layout already shows.
- doc content: facts and invariants, stated as facts; directives belong in a guide.
- reasoning: no `because` or `so` clauses, rejected alternatives, history or motivation in guides or docs; the why goes in a code comment (`agents/code/comments.md`) or the commit message.
- decisions: no decision logs, changelogs or dated "we chose" records; the current fact goes in its doc, the rule in its guide.
- form: one statement per fact; a table when facts share attributes; no prose a table or bullet can carry.
- numbers: result numbers (errors, gains, coverage, effects) live only in `docs/results/`, each table naming its source artifact; experiment measurements live in `docs/evidence/`; every other file links there.
- language: plain words; no em dashes; no bold as decoration; sentence-case headings that name what the section holds; no sentence that describes the document itself; no filler, staged run-ups, triads by habit or inflated words (crucial, robust, seamless, leverage, showcase).

## Workflow
- add a doc: write it from the template, then add its line to the folder's `index.md` (a guide: a `## Route` or `## Calls` line instead).
- modify: change only the stale statement; keep headings, they are link targets.
- finish: `make docs-lint`.

## Templates
- entry (`AGENTS.md`): `## Route` · `## Rules` · `## File structure`
- guide: `## Calls` · `## Rules` · `## Workflow`; omit empty sections; workflow lines are one-line cross-file obligations or non-obvious order
- index (`index.md` in every docs folder): title + one map
- map: flat `path : responsibility` lines, sorted by path, one code block, no tree glyphs, no padding
- fact doc: facts and invariants only; architecture docs start with `## Diagram` (Mermaid) when a picture carries the structure, then tables
- results doc: one table per measurement, each preceded by a `Source:` line naming the artifact and the command that writes it
