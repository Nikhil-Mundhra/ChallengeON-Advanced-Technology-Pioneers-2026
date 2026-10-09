"""Fitted-model evaluation (models/evaluate.py: score a saved model without refitting)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from tourism_twin.models.composite import AdditiveLogModel
from tourism_twin.models.fitters import JointLinear
from synthetic import _synthetic, _components


def test_saved_model_scores_identically_and_refuses_its_training_window(tmp_path):
    from tourism_twin.models.evaluate import card_for, evaluate_fitted, load_model, save_model

    frame = _synthetic(noise=0.02)
    train, later = frame[frame["date"] < "2024-07-01"], frame[frame["date"] >= "2024-07-01"].copy()
    model = AdditiveLogModel(_components(), fitter=JointLinear()).fit(train)
    path = save_model(model, card_for("toy", train), tmp_path / "toy.pkl")
    loaded, card = load_model(path)
    assert card.train_end == "2024-06-30" and card.markets == ("M",)
    np.testing.assert_array_equal(loaded.predict(later).to_numpy(), model.predict(later).to_numpy())

    first = evaluate_fitted(loaded, later, card)
    second = evaluate_fitted(loaded, later, card)  # no refit: scoring twice changes nothing
    pd.testing.assert_frame_equal(first.metrics, second.metrics)
    with pytest.raises(ValueError, match="on or before the model's last training day"):
        evaluate_fitted(loaded, frame, card)


class _Shifted:
    """A fitted stand-in whose prediction is the actual target times a constant."""

    def __init__(self, factor: float) -> None:
        self.factor = factor

    def fit(self, panel):
        return self

    def predict(self, panel):
        return panel["guests"] * self.factor


def test_scorecard_metrics_grains_direction_and_coverage():
    from tourism_twin.models.evaluate import evaluate_fitted

    frame = _synthetic(noise=0.05).assign(market="DOMESTIC")
    exact = evaluate_fitted(_Shifted(1.0), frame)
    assert (exact.metrics["wmape"] == 0).all() and (exact.metrics["mse"] == 0).all()
    assert (exact.direction["hit_rate"] == 1.0).all()  # same totals, same direction every period
    assert set(exact.metrics["grain"]) == {"day", "week", "month"}
    weeks = exact.metrics.set_index("grain").loc["week", "n"]
    assert weeks == 104  # only complete Monday–Sunday weeks of 730 days starting on a Sunday

    high = evaluate_fitted(_Shifted(1.1), frame).metrics.set_index("grain")
    assert high.loc["day", "bias"] == pytest.approx(0.1) and high.loc["month", "wmape"] == pytest.approx(0.1)
    assert high.loc["day", "log_mse"] == pytest.approx(np.log(1.1) ** 2)

    band = pd.DataFrame({"lower": frame["guests"] * 0.95, "upper": frame["guests"] * 1.05}, index=frame.index)
    band.iloc[::4] = band.iloc[::4] * 2  # a quarter of the days miss the band
    covered = evaluate_fitted(_Shifted(1.0), frame, intervals=band).coverage
    assert covered.loc[0, "coverage"] == pytest.approx(0.75, abs=0.002)
