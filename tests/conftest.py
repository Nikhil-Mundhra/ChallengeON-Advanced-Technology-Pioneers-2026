from __future__ import annotations

import pandas as pd
import pytest

from tourism_twin.config import SETTINGS
from tourism_twin.data.daily_panel import build_daily_panel
from tourism_twin.planning.simulator import TourismDigitalTwin

from synthetic import _calendar_conv_frame


@pytest.fixture(scope="session")
def twin() -> TourismDigitalTwin:
    return TourismDigitalTwin()


@pytest.fixture(scope="session")
def weekly_panel() -> pd.DataFrame:
    return pd.read_parquet(SETTINGS.panel_path)


@pytest.fixture(scope="session")
def daily_panel() -> pd.DataFrame:
    return build_daily_panel()


@pytest.fixture(scope="session")
def _kernel_frame_once() -> pd.DataFrame:
    return _calendar_conv_frame()


@pytest.fixture
def kernel_frame(_kernel_frame_once) -> pd.DataFrame:
    """The synthetic arrivals-kernel frame (synthetic._calendar_conv_frame), built once per session;
    each test gets its own copy to modify."""
    return _kernel_frame_once.copy()
