# Presentation deck

## Calls
- `meta/deck/README.md` : slide types, keys, number placeholders, build commands, writing rules for slide text

## Rules
- content: slide content is edited only in `meta/deck/deck.yaml`: exactly 10 slides, one `type` each (cover, columns, rows, hero, stats, flow, table, chart).
- design: tokens (colours, type sizes, spacing, grid ratios) live only in `reporting/deck/theme.py`; every box comes from `grid.py`; text is fitted in `typeset.py`; shapes in `canvas.py`; one renderer per type in `slides/`; background art in `art.py`; the tornado chart in `figures.py`; `reporting/palette.py` stays for the PDF reports.
- build: build and export only through `build_deck`.
- numbers: result numbers on slides (errors, gains, shares, effects) are `{name}` placeholders filled from artifacts (`validation_summary.json`, `outlook.json`, `evaluation_results.json`; `reporting/deck/numbers.py`); never type a result into slide text; every fallback entry names its `source`; design facts (7 validation origins, a 21-day lag window) may be written directly.
- language: plain language; a technical term only with its job; a detail always under its parent bullet.
