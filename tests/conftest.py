from __future__ import annotations

import pandas as pd
import pytest

from tourism_twin.config import SETTINGS
from tourism_twin.data.daily_panel import build_daily_panel
from tourism_twin.services.simulator import TourismDigitalTwin


@pytest.fixture(scope="session")
def twin() -> TourismDigitalTwin:
    return TourismDigitalTwin()


@pytest.fixture(scope="session")
def weekly_panel() -> pd.DataFrame:
    return pd.read_parquet(SETTINGS.panel_path)


@pytest.fixture(scope="session")
def daily_panel() -> pd.DataFrame:
    return build_daily_panel()
