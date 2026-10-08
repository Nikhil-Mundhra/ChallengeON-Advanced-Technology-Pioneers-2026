"""EventKernel: one smoothed log-effect per day of each event's window, read from events.csv.

Each event type gets one coefficient per day offset in its window (union over occurrences); a
second-difference penalty of strength `smoothing` keeps each kernel smooth. Coefficients are
log effects relative to days outside every window, and the contribution is zero outside them.
Window days never seen in training are reported as unidentified (their values come from the
smoothing penalty).
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

import numpy as np
import pandas as pd

from tourism_twin.domain.events import DEFAULT_KERNEL_EVENTS, load_event_calendar
from tourism_twin.features.events import event_offsets, offset_column
from tourism_twin.models.components.base import LinearComponent


class EventKernel(LinearComponent):
    centred = False  # zero contribution outside every window: the contribution is the event effect

    def __init__(
        self,
        events: Iterable[str] = DEFAULT_KERNEL_EVENTS,
        smoothing: float = 1.0,
        name: str = "events",
        date_column: str = "date",
        calendar: Optional[pd.DataFrame] = None,
    ) -> None:
        super().__init__()
        self.name = name
        self.events = tuple(events)
        self.smoothing = smoothing
        self.date_column = date_column
        self.requires = (date_column,)
        self.calendar = load_event_calendar() if calendar is None else calendar
        unknown = set(self.events) - set(self.calendar["event"])
        if unknown:
            raise ValueError(f"Events not in the calendar: {sorted(unknown)}")
        rows = self.calendar[self.calendar["event"].isin(self.events)]
        self.offsets = {
            event: list(range(int(g["window_start_offset"].min()), int(g["window_end_offset"].max()) + 1))
            for event, g in rows.groupby("event")
        }

    def _columns(self):
        return [(event, k) for event in self.events for k in self.offsets[event]]

    def design(self, panel: pd.DataFrame) -> pd.DataFrame:
        offsets = event_offsets(panel[self.date_column], self.calendar, self.events)
        columns = {
            f"{event}@{k:+d}": (offsets[offset_column(event)] == k).astype(float)
            for event, k in self._columns()
        }
        return pd.DataFrame(columns, index=panel.index)

    def penalty_rows(self) -> Optional[np.ndarray]:
        """Second differences of each event's kernel, scaled by sqrt(smoothing)."""
        width = len(self._columns())
        rows, start = [], 0
        for event in self.events:
            n = len(self.offsets[event])
            for i in range(n - 2):
                row = np.zeros(width)
                row[start + i:start + i + 3] = (1.0, -2.0, 1.0)
                rows.append(row)
            start += n
        return np.sqrt(self.smoothing) * np.array(rows) if rows else None

    def explain(self) -> Dict[str, Any]:
        self._require_fitted()
        kernels: Dict[str, Dict[int, float]] = {}
        for (event, k), coef in zip(self._columns(), self.coef_):
            kernels.setdefault(event, {})[k] = float(np.expm1(coef))
        out: Dict[str, Any] = {"effect_pct_by_day_offset": kernels, "smoothing": self.smoothing}
        if self.unidentified_:
            out["unidentified"] = list(self.unidentified_)
        return out
