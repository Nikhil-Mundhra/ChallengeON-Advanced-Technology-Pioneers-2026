"""Reader of the lake: curated Parquet tables, and SQL over them through DuckDB views.

The panels read through here. The views make the curated tables queryable without the
generated analytics.duckdb file. models/ still read the panel Parquet directly.
"""

from __future__ import annotations

import duckdb
import pandas as pd

from tourism_twin.config import SETTINGS, Settings


class LakeRepository:
    def __init__(self, settings: Settings = SETTINGS):
        self.settings = settings

    def guests(self) -> pd.DataFrame:
        return pd.read_parquet(self.settings.guest_daily_path)

    def flights(self) -> pd.DataFrame:
        return pd.read_parquet(self.settings.flight_daily_path)

    def weekly_panel(self) -> pd.DataFrame:
        return pd.read_parquet(self.settings.panel_path)

    def daily_panel(self) -> pd.DataFrame:
        return pd.read_parquet(self.settings.daily_panel_path)

    def sql(self) -> duckdb.DuckDBPyConnection:
        """In-memory DuckDB connection exposing guest_daily and flight_daily as views over Parquet."""
        connection = duckdb.connect()
        for view, path in (("guest_daily", self.settings.guest_daily_path), ("flight_daily", self.settings.flight_daily_path)):
            escaped = str(path).replace("'", "''")
            connection.execute(f"CREATE VIEW {view} AS SELECT * FROM read_parquet('{escaped}')")
        return connection
