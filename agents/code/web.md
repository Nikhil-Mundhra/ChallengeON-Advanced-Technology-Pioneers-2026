# Web app

## Calls
- `agents/code/comments.md` : comment rules for every changed line
- `agents/data/artifacts.md` : regenerating and committing the bundle
- `docs/architecture/web-bundle.md` : bundle files, engine modules, source layout
- `docs/guide/web.md` : pages, commands, deploy

## Rules
- backend: static site with no request-time backend; never add an API or BFF for model numbers (the bundle is the store).
- engine: model numbers are computed only in `web/src/engine/`; components and features call it and format, with no model arithmetic; every new engine function gets a vitest case.
- parity: every engine port gets golden cases in `export/bundle.golden_part` (or `planning_golden`) and a parity test; tolerance 1e-9 where the maths is exact.
- routes: defined only in `web/src/app/routes.tsx`.
- format: numbers and dates only through `web/src/data/format.ts`; charts styled only through `web/src/components/charts/theme.ts`; sliders use `SliderRow` with a `defaultValue`.
- names: market names only through `content/labels.marketName`.
- questions: the five planning answers are computed only in `engine/questions.ts` and rendered only by `features/questions/QuestionAnswers` (landing and report); their numbers never appear in copy.
- simulate: `SimulatePage.tsx` stays a container for shared state; new UI goes in its own pane component; slider availability per market is decided only in `levers.sliderAvailability`; scenario levers never change real weeks and start after the real data by default.
- css: CSS used by more than one feature lives in `components/*` or `theme/`, never in a lazy-loaded feature's CSS.
- colour: only the semantic tokens in `web/src/theme/tokens.css`; no hex outside it; no `--brand-*` outside the brand surfaces (top nav, pills, landing, report hero); every new colour token gets a dark-mode value.
- copy: plain language; no statistical term beyond "±X% error"; no em dashes; a landing statement calls a change up or down only when it exceeds the forecast's own error (`engine/insights.ts`), otherwise "about the same".
- map: "Leaving" on the moving map is check-ins minus the change in guests staying (`engine/playback.ts`), never a stay-length model.
- report: report copy lives in `web/src/content/report.ts`; each number names its source file in `docs/results/`.
- checks: `make web-test` and `npx tsc --noEmit` in `web/` before a commit that touches `web/`.
