"""The chains compared: the shipped seat chain and its link 1 with a seasonal strength, per form and ridge.
Everything else (link 2, knots, cap, pooled base share, smearing) is the shipped spec."""

from __future__ import annotations

from dataclasses import fields
from typing import Dict

from tourism_twin.planning.chain import ChainSpec
from tourism_twin.planning.specs import CHAIN_SPECS

from seasonal_kernel import NAME, SeasonalChainSpec

SHIPPED = "shipped"
FORMS = {"season": 0, "fourier1": 1, "fourier2": 2}  # form label -> harmonics (0: season one-hot)
RIDGES = (0.001, 0.01, 0.1, 1.0)


def name(form: str, ridge: float) -> str:
    return f"{form}_r{ridge:g}"


def seasonal(form: str, ridge: float) -> ChainSpec:
    shipped = CHAIN_SPECS["seat_chain"]
    params = {**shipped._seat_kernel_params(), "form": "season" if form == "season" else "fourier",
              "harmonics": max(FORMS[form], 1), "strength_ridge": ridge}
    arrivals = shipped.arrivals.replace_component("seat_kernel", (NAME, params))
    return SeasonalChainSpec(**{**{f.name: getattr(shipped, f.name) for f in fields(shipped)}, "arrivals": arrivals})


SPECS: Dict[str, ChainSpec] = {SHIPPED: CHAIN_SPECS["seat_chain"],
                               **{name(f, r): seasonal(f, r) for f in FORMS for r in RIDGES}}


def complexity(label: str) -> int:
    """Free parameters per market beyond the shipped chain: 3 for a season (4 minus mean zero), 2 per harmonic pair."""
    if label == SHIPPED:
        return 0
    form = label.split("_")[0]
    return 3 if form == "season" else 2 * FORMS[form]

