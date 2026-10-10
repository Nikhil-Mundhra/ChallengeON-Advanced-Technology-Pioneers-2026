# Presentation deck

Edit `deck.yaml`, then build:

```bash
twin validate && twin outlook   # numbers the deck reads (validation_summary.json, outlook.json)
twin report deck                # output/deck/deck.pptx and deck.pdf (PDF needs LibreOffice)
twin report deck --previews     # also one PNG per slide in output/deck/previews (needs pdftoppm)
twin report deck --no-pdf       # PowerPoint only
```

The PowerPoint is fully editable: real text boxes, each with a stable name (`title`, `hero.value`, `col2.head`, `bg.routes`, ...) shown in PowerPoint's selection pane. Changes made there are not written back to `deck.yaml`.

## Slides

The deck has exactly 10 slides. Every slide has `type`, `kicker` (small label above the title), `title`, `subtitle` (one line, directly under the title), `notes` (speaker notes) and an optional `footnote`. `tone: dark` puts a content slide on the navy background (the cover is always dark).

| `type` | Keys |
| --- | --- |
| `cover` | `title`, `subtitle`, `line` (a short accent line) |
| `columns` | `columns`: 2 to 4 items of `head`, `body` (numbered 01, 02, ...) |
| `rows` | `rows`: up to 6 items of `head`, `body` (numbered) |
| `hero` | `hero`: `value`, `label`; `side`: short lines; `side_note` |
| `stats` | `stats`: 3 items of `label`, `value`, `caption` (label and caption at most 2 lines) |
| `flow` | `flow`: rows of `label` (optional) and `steps` (3 to 6 boxes of `head`, `detail`), joined by arrows |
| `table` | `table`: `header`, `rows`, `widths` (column fractions), `highlight_row` (0-based); optional `side`, `side_note` |
| `chart` | `figure` (`tornado`), `scenario` (the named scenario it draws), `side`, `side_note` |

Inline accents in any string: `**text**` is bold, `==text==` is bold in the accent colour. Use one or two per slide, on the key number or claim. A non-breaking space (` ` in a double-quoted string) keeps two words on one line.

## Numbers

Write numbers as `{name}`. Hero and stat values must be placeholders; the build fails on a typed number there, on an unknown name and on text that does not fit its box.

| Prefix | Source |
| --- | --- |
| `val.*`, `cmp.*`, `nat.*` | `output/validation_summary.json` (`twin validate`) |
| `outlook.*` | `output/outlook.json` (`twin outlook`) |
| `plan.<model>.wmape`, `plan.coverage_pct` | `lake/curated/evaluation_results.json` (weekly planning back-test; models `prior`, `calendar`, `structural`, `hybrid`) |
| `scen.<id>.*` | the planning simulator, for each entry under `scenarios:` |

A scenario names a `market`, a `season` and any lever (`delta_frequency`, `aircraft_gauge`, `delta_seats_pct`, `delta_load_factor`, `delta_p2p_share`, ...). It yields `visitors_base`, `visitors_sim`, `visitors_delta` (weekly hotel check-ins), `nights_base`, `nights_sim`, `nights_delta` (weekly hotel nights), `p10`, `p90` (the stated range of weekly nights) and `lever1..3` with `lever1..3_share` (the levers that move nights most around it).

The `numbers:` block is the fallback when an artifact is missing; every entry names its `source`. The build lists numbers still taken from it.

## Look

Tokens (colours, type sizes, spacing, grid ratios) live only in `src/tourism_twin/reporting/deck/theme.py`; every box comes from `grid.py`. Light content slides sit between a dark cover and a dark closing slide, with one accent colour and no shadows or accent bars. Background art (a faint square grid and flight routes into Abu Dhabi) is drawn by `art.py`. Fonts: Open Sans in `fonts/` (SIL Open Font License, `fonts/OFL.txt`); install them so the PDF export and the text measurement match.

## Writing rules

- Plain, short words; sentence case titles of at most 9 words, no full stop at the end.
- At most about 45 words of body per slide; the detail goes in `notes`.
- No dashes as punctuation: use commas, colons or full stops.
