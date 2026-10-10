# Presentation deck

Edit `deck.yaml`, then build:

```bash
twin validate && twin outlook  # numbers the deck reads (outlook.json is required: slide 9)
twin report deck            # output/deck/deck.pptx and deck.pdf (PDF needs LibreOffice)
twin report deck --no-pdf   # PowerPoint only
```

The PowerPoint is fully editable (real text boxes), so final touches can also be made in PowerPoint or Google Slides. Changes made there are not written back to `deck.yaml`.

## Editing `deck.yaml`

| Key | Meaning |
| --- | --- |
| `layout` | `cover` for the title slide (`kicker`, `title`, `message`, `cards`); omit for content slides |
| `title` | Slide title |
| `message` | One line under the title: the slide's takeaway |
| `bullets` | Check-icon list: `text` is a bold line, `children` its short grey lines |
| `stats` | Big-number tiles in a row: `value`, `label`, `tone` (`green`, `dark`, `red`, `sand`) |
| `cards` | Solid tiles in a row: `title`, `lines`, `tone` |
| `band_position` | `top` puts `stats`/`cards` above the rest of the body; default bottom (full body when alone) |
| `figure` | A generated figure (`system_diagram`, `conversion_chain`, `model_form`, `validation_bars`, `protocol_timeline`, `outlook_months`, `waterfall`, `tornado`), or `asset:<file>` for an image in `assets/` |
| `figure_position` | `top` puts the figure full width above the bullets; otherwise it sits to the right |
| `table` | `header` and `rows`; `widths` (column fractions); `highlight_row` (0-based) is emphasised |
| `notes` | Speaker notes |

## Look

UAE flag colours with a sand neutral and Open Sans (`reporting/deck/theme.py`). The PDF export uses Open Sans only if it is installed: install the files in `fonts/` (SIL Open Font License, `fonts/OFL.txt`).

## Numbers

Write numbers as `{name}`. They are filled from saved results: `output/validation_summary.json` (`twin validate`: `val.*`, `cmp.*`, `nat.*`), `output/outlook.json` (`twin outlook`: `outlook.*`), `lake/curated/evaluation_results.json`, and the planning simulator's reference scenario. The `numbers:` block at the top of `deck.yaml` is the fallback, and every entry must name its `source`. The build lists numbers still taken from the fallback.

## Writing rules

- Plain words. A technical term only together with its job: "We used a distributed lag to turn recent check-ins into guests staying tonight."
- A detail always sits under its parent bullet; one short line per detail.
- One message per slide.
- Screenshots: put the image in `assets/` (e.g. `assets/demo.png`) and reference it as `asset:demo.png`.
