"""Single source of truth for every filesystem location the digital twin reads or writes.

Each location defaults to its place in the repository checkout and can be overridden
through an environment variable, read once when this module is first imported:

    TWIN_ROOT        repository root (default: two levels above src/tourism_twin/)
    TWIN_SOURCE_DIR  raw competition workbooks (default: <root>/01a - DCT Dataset)
    TWIN_LAKE_DIR    DuckDB database, manifest, curated tables, model artifacts (default: <root>/lake)
    TWIN_OUTPUT_DIR  generated figures and PDF reports (default: <root>/output)

Stdlib-only on purpose: the research container imports it without pandas installed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_path(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    return Path(value).expanduser().resolve() if value else default


@dataclass(frozen=True)
class Settings:
    root: Path
    source_dir: Path
    lake_dir: Path
    output_dir: Path

    @classmethod
    def from_env(cls) -> "Settings":
        root = _env_path("TWIN_ROOT", Path(__file__).resolve().parents[2])
        return cls(
            root=root,
            source_dir=_env_path("TWIN_SOURCE_DIR", root / "01a - DCT Dataset"),
            lake_dir=_env_path("TWIN_LAKE_DIR", root / "lake"),
            output_dir=_env_path("TWIN_OUTPUT_DIR", root / "output"),
        )

    @property
    def curated_dir(self) -> Path:
        return self.lake_dir / "curated"

    @property
    def database_path(self) -> Path:
        return self.lake_dir / "analytics.duckdb"

    @property
    def manifest_path(self) -> Path:
        return self.lake_dir / "manifest.json"

    @property
    def guest_daily_path(self) -> Path:
        return self.curated_dir / "guest_daily.parquet"

    @property
    def flight_daily_path(self) -> Path:
        return self.curated_dir / "flight_daily.parquet"

    @property
    def flight_monthly_path(self) -> Path:
        return self.curated_dir / "flight_monthly.parquet"

    @property
    def panel_path(self) -> Path:
        return self.curated_dir / "weekly_market_panel.parquet"

    @property
    def daily_panel_path(self) -> Path:
        return self.curated_dir / "daily_market_panel.parquet"

    @property
    def calibration_path(self) -> Path:
        return self.curated_dir / "structural_calibration.json"

    @property
    def residual_model_path(self) -> Path:
        return self.curated_dir / "residual_engine.pkl"

    @property
    def conformal_path(self) -> Path:
        return self.curated_dir / "conformal_calibrator.json"

    @property
    def evaluation_results_path(self) -> Path:
        return self.curated_dir / "evaluation_results.json"

    @property
    def figures_dir(self) -> Path:
        return self.output_dir / "figures"

    @property
    def pdf_dir(self) -> Path:
        return self.output_dir / "pdf"

    def display_path(self, path: Path) -> str:
        """Repository-relative form for manifests and logs; absolute when outside the root."""
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return str(path)


SETTINGS = Settings.from_env()
