"""Derived features, declared once in PANEL_FEATURES and requested by name by each panel."""

from tourism_twin.features import calendar, flags, lags, ratios  # noqa: F401  (registers the specs)
from tourism_twin.features.registry import PANEL_FEATURES, FeatureRegistry, FeatureSpec, Kind

__all__ = ["PANEL_FEATURES", "FeatureRegistry", "FeatureSpec", "Kind"]
