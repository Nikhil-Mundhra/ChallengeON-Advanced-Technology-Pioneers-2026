# Slope and events

Source: second probe (reference spec with box events), one component switched at a time; unmerged branch. WAPE %.

| Variant | DOM reference (2) | DOM rolling-13 | DOM Aug to Jan | INTL reference (2) | INTL rolling-13 | INTL Aug to Jan |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| No slope, events | 5.10 | 6.70 | 7.45 | 4.92 | 5.11 | 5.10 |
| Slope, events | 4.65 | 4.72 | 4.92 | 4.25 | 5.34 | 5.68 |
| Slope, no events | 4.72 | 4.65 | 4.74 | 4.07 | 5.16 | 5.89 |
| No slope, no events | n/a | n/a | n/a | 4.68 | 5.08 | 5.45 |
| Seasonal naive 364 | 16.31 | 18.8 | n/a | 18.59 | 19.28 | n/a |

Rolling-13: monthly origins 2024-02-01 → 2025-02-01, 6-month horizon. Aug to Jan: test 2024-08-01 → 2025-01-31, the only fold containing National Day and Christmas to New Year.

| Finding |
| --- |
| Slope: DOMESTIC improves on every fold set (up to 2.5 points; fitted −3.9%/yr); INTERNATIONAL improves only on the two February to July reference folds and loses on rolling-13 and Aug to Jan (fitted +7.2%/yr) |
| Events: DOMESTIC is better without them on rolling-13 and Aug to Jan; INTERNATIONAL gains 0.35 on the event fold and is neutral on rolling-13 |
| The two reference folds alone select a different international spec than rolling origins and the event fold |
