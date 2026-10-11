"""ArrivalsConvolution: hotel guests as a stock fed by the flow of new arrivals.

    flow_t = c_t + sum_{k=0..K} w_k * Arrivals_{t-k},   contribution = log(flow_t)

w_k are the kernel weights linking past arrivals to today's guest stock: w_k >= 0,
non-increasing, w_0 <= 1. They are a fitting device, not measured stay lengths, and sum(w) is
not reported as a length of stay (pooled markets mix nationalities). c_t >= 0 is a slowly varying
base stock (guests not explained by recent arrivals), piecewise linear between knots and flat beyond
the training days. With base="arrivals", c_t = rho * (trailing 90-day mean arrivals), rho >= 0: the
base stock then moves with the arrival level, so a carrier exit that halves arrivals also shrinks it.

The maths (constraints, raw-scale warm start, log refinement) is shared with every input kernel in
models/components/convolution.py; this class only names the input: arrival lags from the panel
(arrivals_lag_k), so the first predicted days see the last training days' arrivals. Owns the level.
"""

from __future__ import annotations

from tourism_twin.features.lags import lag_column
from tourism_twin.models.components.convolution import ConvolutionKernel


class ArrivalsConvolution(ConvolutionKernel):
    def __init__(self, max_lag: int = 21, knot_days: int = 365, base_smoothing: float = 1.0,
                 name: str = "arrivals", date_column: str = "date", base: str = "knots") -> None:
        if base not in ("knots", "arrivals"):
            raise ValueError(f"base must be 'knots' or 'arrivals', got {base!r}")
        self.base = base
        super().__init__([lag_column(k) for k in range(max_lag + 1)], knot_days=knot_days, base_smoothing=base_smoothing,
                         name=name, date_column=date_column, base_column="arrivals_mean_90" if base == "arrivals" else None,
                         base_explain_key="base_stock_per_mean_arrival")
