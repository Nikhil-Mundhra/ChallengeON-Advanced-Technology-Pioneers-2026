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
    assert "Domestic error 9.9%" in texts and "1 / 3" in texts
    assert any("Parent" in t and "child two" in t and "grandchild" in t for t in texts)
    assert deck.slides[0].notes_slide.notes_text_frame.text == "notes 8.8"
    assert "val.twin_daily.domestic" in result.fallback_numbers  # still the deck's own value, flagged


def test_artifacts_override_the_deck_fallback(tmp_path):
    summary = tmp_path / "validation_summary.json"
    summary.write_text(json.dumps({"segment_wape": {"twin_daily": {"domestic": 4.18, "international": 4.59}}}))
    table = numbers.collect(FIXTURE["numbers"], summary, tmp_path / "missing.json")
    assert table["val.twin_daily.domestic"].value == "4.2"
    assert table["val.twin_daily.domestic"].source.startswith("validation_summary.json")
    assert table["val.naive_364.domestic"].value == "20.0"  # not in the artifact: fallback stays


def test_unresolved_or_unsourced_numbers_fail_loudly(tmp_path):
    with pytest.raises(KeyError, match="no_such_number"):
        numbers.fill("{no_such_number}", {})
    with pytest.raises(ValueError, match="needs both 'value' and 'source'"):
        numbers.from_deck({"x": {"value": "1"}})
    with pytest.raises(KeyError, match="Unknown figure"):
        build_deck(_write(tmp_path, {**FIXTURE, "slides": [{"title": "t", "figure": "nope"}]}), out_dir=tmp_path / "o",
                   pdf=False, validation_summary=tmp_path / "m.json", planning_evaluation=tmp_path / "m.json")


def test_the_shipped_deck_has_ten_slides_and_every_number_resolves():
    deck = yaml.safe_load(DEFAULT_CONTENT.read_text())
    assert len(deck["slides"]) == 10
    table = numbers.collect(deck.get("numbers", {}), DEFAULT_CONTENT.parent / "absent.json", DEFAULT_CONTENT.parent / "absent.json")
    for slide in deck["slides"]:
        text = yaml.safe_dump(slide)
        for name in numbers.PLACEHOLDER.findall(text):
            assert name in table, f"slide {slide['title']!r}: unresolved {{{name}}}"
