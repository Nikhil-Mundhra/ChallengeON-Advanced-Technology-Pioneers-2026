"""Event calendar.

events.csv is the event registry: one row per occurrence (event type, kind, anchor date, the
day window around the anchor, the markets it applies to, provenance). Event kernels read it.

HOLIDAY_WEEKS and MAJOR_EVENT_WEEKS are the legacy Monday week-start sets behind the
is_holiday_week / is_major_event_week flags of the weekly panel and the residual layer. They are
kept unchanged so the shipped models and their published results stay reproducible; they are not
derived from events.csv (deriving them would move several weeks).
"""

from __future__ import annotations

from functools import lru_cache
from importlib.resources import files

import pandas as pd

from tourism_twin.domain.markets import MODELED_MARKETS, REGIONAL_CLUSTERS

EVENT_KINDS = ("lunar", "solar", "one_off")
EVENT_SCOPES = ("all", "domestic", "international")  # or one market (CHINA) or pooled-market nationality (MOROCCO)

# Event types fitted by EventKernel by default. new_years_eve is excluded: its window lies inside
# christmas_new_year every year, so a separate kernel is not identifiable.
DEFAULT_KERNEL_EVENTS = (
    "ramadan",
    "eid_al_fitr",
    "eid_al_adha",
    "islamic_new_year",
    "prophets_birthday",
    "national_day",
    "christmas_new_year",
    "f1_grand_prix",
    "adipec",
)


@lru_cache(maxsize=1)
def load_event_calendar() -> pd.DataFrame:
    """The event registry with parsed dates and absolute window bounds (window_start, window_end)."""
    with files("tourism_twin.domain").joinpath("events.csv").open("r", encoding="utf-8") as handle:
        calendar = pd.read_csv(handle, parse_dates=["anchor_date"])
    unknown = set(calendar["kind"]) - set(EVENT_KINDS)
    if unknown:
        raise ValueError(f"Unknown event kinds in events.csv: {sorted(unknown)}")
    nationalities = {n for members in REGIONAL_CLUSTERS.values() for n in members}
    unknown = set(calendar["scope"]) - set(EVENT_SCOPES) - set(MODELED_MARKETS) - nationalities
    if unknown:
        raise ValueError(f"Unknown event scopes in events.csv: {sorted(unknown)}")
    if (calendar["window_start_offset"] > calendar["window_end_offset"]).any():
        raise ValueError("events.csv has a window whose start offset is after its end offset")
    calendar["window_start"] = calendar["anchor_date"] + pd.to_timedelta(calendar["window_start_offset"], unit="D")
    calendar["window_end"] = calendar["anchor_date"] + pd.to_timedelta(calendar["window_end_offset"], unit="D")
    return calendar


HOLIDAY_WEEKS = {
    # Eid al-Fitr weeks (Monday week-start dates)
    "2023-04-17",
    "2024-04-08",
    "2025-03-31",
    # Eid al-Adha weeks
    "2023-06-26",
    "2024-06-17",
    "2025-06-02",
    # UAE National Day / Commemoration Day weeks
    "2023-11-27",
    "2024-12-02",
    "2025-12-01",
    # New Year / Festive peak weeks
    "2023-01-02",
    "2023-12-25",
    "2024-01-01",
    "2024-12-30",
    "2025-12-29",
    "2026-01-05",
    # 2026 Lunar New Year / Spring Festival & Ramadan Start
    "2026-02-16",
    # 2026 Eid al-Fitr weeks
    "2026-03-16",
    "2026-03-23",
    # 2026 Eid al-Adha weeks
    "2026-05-25",
    # 2026 UAE National Day week
    "2026-11-30",
}

MAJOR_EVENT_WEEKS = {
    # ADIPEC (Abu Dhabi International Petroleum Exhibition & Conference)
    "2023-10-02",
    "2024-11-04",
    "2025-11-03",
    "2026-11-02",
    # Formula 1 Etihad Airways Abu Dhabi Grand Prix (Yas Marina)
    "2023-11-20",
    "2024-12-02",
    "2025-12-01",
    "2026-11-30",  # race Sunday 2026-12-06
}
