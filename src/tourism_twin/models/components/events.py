"""EventKernel: one smoothed log-effect per day of each event's window, read from events.csv.

Each event type gets one coefficient per day offset in its window (union over occurrences). A
second-difference penalty keeps kernels longer than `min_smoothed_days` smooth; its weight is
`smoothing` times the event's number of occurrences, so it stays proportional to the data
behind each coefficient. Short kernels are left unpenalised so sharp peaks are not flattened. Coefficients are
log effects relative to days outside every window, and the contribution is zero outside them.
Window days never seen in training are reported as unidentified (their values come from the
smoothing penalty).
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

import numpy as np
import pandas as pd

from tourism_twin.domain.events import DEFAULT_KERNEL_EVENTS, load_event_calendar
from tourism_twin.features.events import event_offsets, in_scope, offset_column
from tourism_twin.models.components.base import LinearComponent


class EventKernel(LinearComponent):
    group = "holiday"
    centred = False  # zero contribution outside every window: the contribution is the event effect

    def __init__(
        self,
        events: Iterable[str] = DEFAULT_KERNEL_EVENTS,
        smoothing: float = 1.0,
        min_smoothed_days: int = 6,
        name: str = "events",
        date_column: str = "date",
        calendar: Optional[pd.DataFrame] = None,
    ) -> None:
        super().__init__()
        self.name = name
        self.events = tuple(events)
        self.smoothing = smoothing
        self.min_smoothed_days = min_smoothed_days
        self.date_column = date_column
        self.requires = (date_column, "market")
        self.calendar = load_event_calendar() if calendar is None else calendar
        unknown = set(self.events) - set(self.calendar["event"])
        if unknown:
            raise ValueError(f"Events not in the calendar: {sorted(unknown)}")
        rows = self.calendar[self.calendar["event"].isin(self.events)]
        self.offsets = {
            event: list(range(int(g["window_start_offset"].min()), int(g["window_end_offset"].max()) + 1))
            for event, g in rows.groupby("event")
        }
        self.occurrences = rows.groupby("event").size().to_dict()
        scopes = rows.groupby("event")["scope"].unique()
        mixed = [event for event, values in scopes.items() if len(values) > 1]
        if mixed:
            raise ValueError(f"Events with more than one scope: {mixed}")
        self.scopes = {event: values[0] for event, values in scopes.items()}

    def _columns(self):
        return [(event, k) for event in self.events for k in self.offsets[event]]

    def design(self, panel: pd.DataFrame) -> pd.DataFrame:
        offsets = event_offsets(panel[self.date_column], self.calendar, self.events)
        covered = {event: in_scope(panel["market"], self.scopes[event]).to_numpy() for event in self.events}
        columns = {
            f"{event}@{k:+d}": ((offsets[offset_column(event)] == k) & covered[event]).astype(float)
            for event, k in self._columns()
        }
        return pd.DataFrame(columns, index=panel.index)

    def penalty_rows(self) -> Optional[np.ndarray]:
        """Second differences within each long-enough event kernel (never across events)."""
        width = len(self._columns())
        rows, start = [], 0
        for event in self.events:
            n = len(self.offsets[event])
            if n >= self.min_smoothed_days:
                weight = np.sqrt(self.smoothing * self.occurrences[event])
                for i in range(n - 2):
                    row = np.zeros(width)
                    row[start + i:start + i + 3] = weight * np.array((1.0, -2.0, 1.0))
                    rows.append(row)
            start += n
        return np.array(rows) if rows else None

    def explain(self) -> Dict[str, Any]:
        self._require_fitted()
        kernels: Dict[str, Dict[int, float]] = {}
        for (event, k), coef in zip(self._columns(), self.coef_):
            kernels.setdefault(event, {})[k] = float(np.expm1(coef))
        out: Dict[str, Any] = {"effect_pct_by_day_offset": kernels, "smoothing": self.smoothing}
        if self.unidentified_:
            out["unidentified"] = list(self.unidentified_)
        return out
