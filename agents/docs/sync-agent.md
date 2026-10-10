# Sync agent

## Calls
- `agents/docs/sync-docs.md` : `last synced:`, unchecked changes, owning map, report format

## Rules
- scope: `AGENTS.md`, `CLAUDE.md` and every file in `agents/`: `## Route`, `## Calls`, `## Rules`, `## File structure`.

## Workflow
1. Changed root entries: fix their lines in the `AGENTS.md` `## File structure` map.
2. New area that needs its own directives: a guide in `agents/` plus a `## Route` line in `AGENTS.md`.
3. Added, removed or renamed guide: its `## Route` line and every `## Calls` line naming it.
4. Added or removed skill in `.agents/skills/`: the skills `## Route` line in `AGENTS.md`.
5. `cp AGENTS.md CLAUDE.md`, `make docs-lint`, report, set `last synced:` in `agents/docs/sync-docs.md`.
