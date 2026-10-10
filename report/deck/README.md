# Presentation deck

Edit `deck.yaml`, then build:

```bash
twin report deck            # output/deck/deck.pptx and deck.pdf (PDF needs LibreOffice)
twin report deck --no-pdf   # PowerPoint only
```

The PowerPoint is fully editable (real text boxes), so final touches can also be made in PowerPoint or Google Slides. Changes made there are not written back to `deck.yaml`.

## Editing `deck.yaml`

| Key | Meaning |
| --- | --- |
| `title` | Slide title |
| `message` | One line under the title: the slide's takeaway |
| `bullets` | A tree: `text` is a parent line, `children` its lines one level in |
| `figure` | A generated figure (`goal_tree`, `passenger_split`, `system_diagram`, `conversion_chain`, `validation_bars`, `waterfall`, `tornado`), or `asset:<file>` for an image in `assets/` |
| `figure_position` | `top` puts the figure full width above the bullets; otherwise it sits to the right |
| `table` | `header` and `rows`; `highlight_row` (0-based) is emphasised |
| `notes` | Speaker notes |

## Numbers

Write numbers as `{name}`. They are filled from saved results: `output/validation_summary.json` (`twin validate`), `lake/curated/evaluation_results.json`, and the planning simulator's reference scenario. The `numbers:` block at the top of `deck.yaml` is the fallback, and every entry must name its `source`. The build lists numbers still taken from the fallback.

## Writing rules

- Plain words. A technical term only together with its job: "We used a distributed lag to turn recent check-ins into guests staying tonight."
- A detail always sits under its parent bullet.
- One message per slide.
- Screenshots: put the image in `assets/` (e.g. `assets/demo.png`) and reference it as `asset:demo.png`.
