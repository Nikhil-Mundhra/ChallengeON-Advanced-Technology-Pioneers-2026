"""Presentation deck (reporting/deck): deck.yaml → PPTX, numbers from artifacts and the simulator."""

from __future__ import annotations

import copy
import json
import re
from types import SimpleNamespace

import pytest
import yaml

pptx = pytest.importorskip("pptx")

from tourism_twin.reporting.deck import DEFAULT_CONTENT, DeckContentError, build_deck, numbers  # noqa: E402
from tourism_twin.reporting.deck.typeset import DeckOverflow  # noqa: E402

SHIPPED = yaml.safe_load(DEFAULT_CONTENT.read_text())
TORNADO = [{"lever_name": name, "swing_spread": spread} for name, spread in
           (("P2P Share (+5% / -5%)", 50.0), ("Seat Capacity (+15% / -15%)", 40.0), ("Load Factor (+4% / -4%)", 10.0))]


def _stub_numbers(deck) -> numbers.DeckNumbers:
    """Every placeholder the deck uses, each with a distinct letter-only value ("Qa", "Qb", ...), so a
    digit on a rendered hero or stat can only have been typed into the YAML."""
    names = sorted(set(numbers.PLACEHOLDER.findall(yaml.safe_dump(deck["slides"]))))
    letters = "abcdefghijklmnopqrstuvwxyz"
    table = {name: numbers.Number(f"Q{letters[i // 26]}{letters[i % 26]}", "stub") for i, name in enumerate(names)}
    reports = {spec["scenario"]: SimpleNamespace(tornado_sensitivity=TORNADO)
               for spec in deck["slides"] if spec.get("scenario")}
    return numbers.DeckNumbers(table, reports)


def _build(tmp_path, deck):
    path = tmp_path / "deck.yaml"
    path.write_text(yaml.safe_dump(deck, sort_keys=False, allow_unicode=True))
    result = build_deck(path, out_dir=tmp_path / "out", pdf=False, deck_numbers=_stub_numbers(deck))
    return result, pptx.Presentation(str(result.pptx))


def _shapes(slide):
    return {shape.name: shape for shape in slide.shapes}


def test_the_shipped_deck_builds_ten_named_slides_whose_results_come_from_placeholders(tmp_path):
    result, deck = _build(tmp_path, SHIPPED)
    assert result.slides == len(deck.slides) == 10
    stub_values = {n.value for n in _stub_numbers(SHIPPED).table.values()}
    kinds = [spec["type"] for spec in SHIPPED["slides"]]
    expected = {"cover": "title", "columns": "col1.head", "rows": "row1.head", "hero": "hero.value",
                "stats": "stat1.value", "flow": "flow1.box1", "table": "table.r1.c1", "chart": "chart.figure"}
    for page, (kind, slide) in enumerate(zip(kinds, deck.slides), start=1):
        shapes = _shapes(slide)
        assert {"bg.fill", "bg.grid", "bg.routes", expected[kind]} <= set(shapes), (page, kind)
        assert list(shapes)[0] == "bg.fill"  # background stays behind everything
        assert shapes["page"].text_frame.text == f"{page} / 10"
        assert slide.notes_slide.notes_text_frame.text.strip()
        for name, shape in shapes.items():
            if name == "hero.value" or re.fullmatch(r"stat\d\.value", name):
                text = shape.text_frame.text
                assert any(v in text for v in stub_values), (page, name, text)
                assert not re.search(r"\d", text), f"slide {page} {name}: typed number in {text!r}"


def test_content_rules_fail_the_build(tmp_path):
    typed = copy.deepcopy(SHIPPED)
    stats = next(s for s in typed["slides"] if s["type"] == "stats")
    stats["stats"][0]["value"] = "+42"
    with pytest.raises(DeckContentError, match="placeholder"):
        _build(tmp_path, typed)
    nine = copy.deepcopy(SHIPPED)
    nine["slides"].pop()
    with pytest.raises(DeckContentError, match="10"):
        _build(tmp_path, nine)
    with pytest.raises(KeyError, match="no_such_number"):
        numbers.fill("{no_such_number}", {})


def test_text_that_does_not_fit_raises(tmp_path):
    long = copy.deepcopy(SHIPPED)
    columns = next(s for s in long["slides"] if s["type"] == "columns")
    columns["columns"][0]["body"] = " ".join(["Passengers connect onward to other cities"] * 12)
    with pytest.raises(DeckOverflow):
        _build(tmp_path, long)


def test_scenario_numbers_equal_the_simulator(twin):
    spec = {"market": "united kingdom", "season": "Winter_Peak", "delta_frequency": 2, "aircraft_gauge": 290}
    table, reports = numbers.from_scenarios({"uk": spec}, twin)
    from tourism_twin.domain.scenario import ScenarioLever

    direct = twin.run_scenario("UNITED KINGDOM", "Winter_Peak",
                               ScenarioLever(market="UNITED KINGDOM", delta_frequency=2, aircraft_gauge=290))
    s, h = direct.structural_result, direct.hybrid_result
    value = lambda key: float(table[f"scen.uk.{key}"].value.replace(",", ""))  # noqa: E731
    assert value("visitors_base") == pytest.approx(s.base_arrivals, abs=0.5)
    assert value("visitors_sim") == pytest.approx(s.sim_arrivals, abs=0.5)
    assert value("visitors_delta") == pytest.approx(s.sim_arrivals - s.base_arrivals, abs=0.5)
    assert value("nights_delta") == pytest.approx(h["hybrid_delta"], abs=0.5)
    assert value("nights_sim") == pytest.approx(h["hybrid_sim"], abs=0.5)
    assert value("p10") < value("nights_sim") < value("p90")
    top = max(direct.tornado_sensitivity, key=lambda r: r["swing_spread"])
    assert table["scen.uk.lever1"].value == numbers.lever_name(top)
    with pytest.raises(ValueError, match="Unknown scenario levers"):
        numbers.from_scenarios({"bad": {**spec, "more_planes": 1}}, twin)


def test_artifacts_override_the_deck_fallback(tmp_path):
    summary = tmp_path / "validation_summary.json"
    summary.write_text(json.dumps({  # the shape `twin validate` writes
        "segment_wape": {"grain": "day", "values": {"twin_daily": {"domestic": 4.18, "international": 4.59}}},
        "compare": {"grain": "day", "rows": [{"segment": "domestic", "baseline": "naive_364", "candidate": "twin_daily",
                                              "difference_pp": -12.7, "ci_low": -14.1, "ci_high": -11.2, "share_folds_same_sign": 1.0}]},
        "nationalities": {"pooled_nationalities_vs_split": {"difference_pp": -0.55}}}))
    deck = {"numbers": {"val.twin_daily.domestic": {"value": "9.9", "source": "fixture"},
                        "val.naive_364.domestic": {"value": "20.0", "source": "fixture"}}}
    collected = numbers.collect(deck, summary, tmp_path / "missing.json")
    table = collected.table
    assert table["val.twin_daily.domestic"].value == "4.2"
    assert table["cmp.twin_daily_vs_naive_364.domestic.difference_pp"].value == "-12.70"
    assert table["val.naive_364.domestic"].value == "20.0"  # not in the artifact: fallback stays
    collected.fill("{val.naive_364.domestic} {val.twin_daily.domestic}")
    assert collected.fallbacks(deck["numbers"]) == ["val.naive_364.domestic"]


def _month(m, guests, change=None):
    return {"month": m, "guest_nights": guests, **({} if change is None else {"change_pct": change})}


def test_outlook_numbers(tmp_path):
    path = tmp_path / "outlook.json"
    path.write_text(json.dumps({  # the shape `twin outlook` writes (nowcast/outlook.outlook_document)
        "window": "winter 2026/27", "spec": "twin_daily", "guests_known_to": "2025-07-31", "arrivals_known_to": "2026-02-28",
        "previous": {"window": "2025/26", "guest_nights": 3.0e6,
                     "months": [_month("2025-12", 1.1e6), _month("2026-01", 1.0e6), _month("2026-02", 0.9e6)]},
        "scenarios": {s: {"guest_nights": g, "change_pct": c, "domestic_share_pct": 30.0,
                          "top_source_markets": [{"market": "RUSSIAN FEDERATION", "share_pct": 10.3}],
                          "months": [_month("2026-12", g * 0.36, c), _month("2027-01", g * 0.34, c), _month("2027-02", g * 0.30, c)]}
                      for s, g, c in (("flat", 3.0e6, 0.2), ("trend", 3.2e6, 7.7))},
        "backtest": [{"window": "winter 2024/25 (Dec–Jan)", "scenario": "trend", "segment": "total", "season_error_pct": 29.1}]}))
    table = numbers.from_outlook(path)
    assert (table["outlook.window"].value, table["outlook.previous.guests"].value) == ("2026/27", "3.00")
    assert (table["outlook.trend.guests"].value, table["outlook.trend.change"].value) == ("3.20", "+8")
    assert table["outlook.trend.top1"].value == "Russia"
    assert table["outlook.bt.window"].value == "2024/25 (Dec to Jan)"
    assert table["outlook.bt.trend.total"].value == "+29"
