"""Presentation deck (reporting/deck): content YAML → PPTX, numbers filled from artifacts."""

from __future__ import annotations

import json

import pytest
import yaml

pptx = pytest.importorskip("pptx")

from tourism_twin.reporting.deck import DEFAULT_CONTENT, build_deck, numbers  # noqa: E402

FIXTURE = {
    "footer": "test deck",
    "numbers": {"val.twin_daily.domestic": {"value": "9.9", "source": "fixture"},
                "val.twin_daily.international": {"value": "8.8", "source": "fixture"},
                "val.naive_364.domestic": {"value": "20.0", "source": "fixture"},
                "val.naive_364.international": {"value": "21.0", "source": "fixture"},
                "val.time_only.domestic": {"value": "12.0", "source": "fixture"},
                "val.time_only.international": {"value": "13.0", "source": "fixture"},
                "val.flow_only.domestic": {"value": "10.5", "source": "fixture"},
                "val.flow_only.international": {"value": "9.5", "source": "fixture"}},
    "slides": [
        {"title": "Parent and children", "message": "Domestic error {val.twin_daily.domestic}%",
         "bullets": [{"text": "Parent", "children": ["child one", {"text": "child two", "children": ["grandchild"]}]}],
         "notes": "notes {val.twin_daily.international}"},
        {"title": "Figure on top", "figure": "conversion_chain", "figure_position": "top", "bullets": ["below the figure"]},
        {"title": "Figure and table", "figure": "validation_bars", "bullets": ["left"],
         "table": {"header": ["Model", "Domestic"], "rows": [["Full", "{val.twin_daily.domestic}%"]], "highlight_row": 0}},
    ],
}


def _month(m, guests, change=None):
    return {"month": m, "guest_nights": guests, **({} if change is None else {"change_pct": change})}


OUTLOOK = {  # the shape `twin outlook` writes (nowcast/outlook.outlook_document)
    "window": "winter 2026/27", "spec": "twin_daily", "guests_known_to": "2025-07-31", "arrivals_known_to": "2026-02-28",
    "previous": {"window": "2025/26", "guest_nights": 3.0e6,
                 "months": [_month("2025-12", 1.1e6), _month("2026-01", 1.0e6), _month("2026-02", 0.9e6)]},
    "scenarios": {s: {"guest_nights": g, "change_pct": c, "domestic_share_pct": 30.0,
                      "top_source_markets": [{"market": "RUSSIAN FEDERATION", "share_pct": 10.3}, {"market": "UNITED KINGDOM", "share_pct": 9.1},
                                             {"market": "INDIA", "share_pct": 8.7}],
                      "months": [_month("2026-12", g * 0.36, c), _month("2027-01", g * 0.34, c), _month("2027-02", g * 0.30, c)]}
                  for s, g, c in (("flat", 3.0e6, 0.2), ("trend", 3.2e6, 7.7))},
    "backtest": [{"window": "winter 2024/25 (Dec–Jan)", "scenario": s, "segment": seg, "season_error_pct": e}
                 for s, e in (("flat", -8.9), ("trend", 29.1)) for seg in ("total", "international", "domestic")],
}


def _write(tmp_path, content):
    path = tmp_path / "deck.yaml"
    path.write_text(yaml.safe_dump(content, sort_keys=False))
    return path


def test_deck_builds_slides_fills_numbers_and_reports_fallbacks(tmp_path):
    result = build_deck(_write(tmp_path, FIXTURE), out_dir=tmp_path / "out", pdf=False,
                        validation_summary=tmp_path / "missing.json", planning_evaluation=tmp_path / "missing.json")
    deck = pptx.Presentation(str(result.pptx))
    assert result.slides == len(deck.slides) == 3
    texts = [shape.text_frame.text for shape in deck.slides[0].shapes if shape.has_text_frame]
    assert "Domestic error 9.9%" in texts and "01 / 03" in texts
    assert {"Parent", "child two", "·  grandchild"} <= set(texts)
    assert deck.slides[0].notes_slide.notes_text_frame.text == "notes 8.8"
    assert "val.twin_daily.domestic" in result.fallback_numbers  # still the deck's own value, flagged


def test_artifacts_override_the_deck_fallback(tmp_path):
    summary = tmp_path / "validation_summary.json"
    summary.write_text(json.dumps({  # the shape `twin validate` writes
        "segment_wape": {"grain": "day", "values": {"twin_daily": {"domestic": 4.18, "international": 4.59}}},
        "compare": {"grain": "day", "rows": [{"segment": "domestic", "baseline": "naive_364", "candidate": "twin_daily",
                                              "difference_pp": -12.7, "ci_low": -14.1, "ci_high": -11.2, "share_folds_same_sign": 1.0}]},
        "nationalities": {"pooled_nationalities_vs_split": {"difference_pp": -0.55}}}))
    table = numbers.collect(FIXTURE["numbers"], summary, tmp_path / "missing.json")
    assert table["val.twin_daily.domestic"].value == "4.2"
    assert table["cmp.twin_daily_vs_naive_364.domestic.difference_pp"].value == "-12.70"
    assert table["nat.pooled_nationalities_vs_split.difference_pp"].value == "-0.55"
    assert table["val.twin_daily.domestic"].source.startswith("validation_summary.json")
    assert table["val.naive_364.domestic"].value == "20.0"  # not in the artifact: fallback stays


def test_outlook_numbers_and_figure(tmp_path):
    path = tmp_path / "outlook.json"
    path.write_text(json.dumps(OUTLOOK))
    table = numbers.from_outlook(path)
    assert table["outlook.window"].value == "2026/27"
    assert (table["outlook.trend.change"].value, table["outlook.flat.change"].value) == ("+8", "+0")
    assert (table["outlook.trend.top1"].value, table["outlook.trend.top1_share"].value) == ("Russia", "10")
    assert table["outlook.month1"].value == "Dec 2026"
    assert table["outlook.bt.trend.total"].value == "+29"
    content = {**FIXTURE, "slides": [{"title": "Outlook {outlook.window}", "figure": "outlook_months", "bullets": ["{outlook.trend.top2}"]}]}
    result = build_deck(_write(tmp_path, content), out_dir=tmp_path / "o", pdf=False, validation_summary=tmp_path / "m.json",
                        planning_evaluation=tmp_path / "m.json", outlook=path)
    texts = [s.text_frame.text for s in pptx.Presentation(str(result.pptx)).slides[0].shapes if s.has_text_frame]
    assert "Outlook 2026/27" in texts and any("the UK" in t for t in texts)


def test_cover_cards_and_stat_tiles_render_with_numbers(tmp_path):
    content = {**FIXTURE, "slides": [
        {"layout": "cover", "kicker": "k", "title": "Cover", "message": "m",
         "cards": [{"title": "Predict", "lines": ["daily"], "tone": "dark"}, {"title": "Explain", "tone": "red"}]},
        {"title": "Stats", "stats": [{"value": "{val.twin_daily.domestic}%", "label": "domestic"}], "figure": "validation_bars"},
        {"title": "Cards only", "cards": [{"title": "Limits", "lines": ["one", "two"], "tone": "sand"}]},
    ]}
    result = build_deck(_write(tmp_path, content), out_dir=tmp_path / "o", pdf=False,
                        validation_summary=tmp_path / "m.json", planning_evaluation=tmp_path / "m.json")
    deck = pptx.Presentation(str(result.pptx))
    texts = lambda i: [s.text_frame.text for s in deck.slides[i].shapes if s.has_text_frame]  # noqa: E731
    assert "Cover" in texts(0) and any("Predict" in t and "daily" in t for t in texts(0))
    assert "9.9%" in texts(1) and any("Limits" in t and "two" in t for t in texts(2))


def test_unresolved_or_unsourced_numbers_fail_loudly(tmp_path):
    with pytest.raises(KeyError, match="no_such_number"):
        numbers.fill("{no_such_number}", {})
    with pytest.raises(ValueError, match="needs both 'value' and 'source'"):
        numbers.from_deck({"x": {"value": "1"}})
    with pytest.raises(KeyError, match="Unknown figure"):
        build_deck(_write(tmp_path, {**FIXTURE, "slides": [{"title": "t", "figure": "nope"}]}), out_dir=tmp_path / "o",
                   pdf=False, validation_summary=tmp_path / "m.json", planning_evaluation=tmp_path / "m.json")


def test_the_shipped_deck_has_ten_slides_and_every_number_resolves(tmp_path):
    deck = yaml.safe_load(DEFAULT_CONTENT.read_text())
    assert len(deck["slides"]) == 10
    outlook = tmp_path / "outlook.json"
    outlook.write_text(json.dumps(OUTLOOK))
    table = numbers.collect(deck.get("numbers", {}), tmp_path / "absent.json", tmp_path / "absent.json", outlook)
    for slide in deck["slides"]:
        text = yaml.safe_dump(slide)
        for name in numbers.PLACEHOLDER.findall(text):
            assert name in table, f"slide {slide['title']!r}: unresolved {{{name}}}"
