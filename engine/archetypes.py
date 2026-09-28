"""Market archetype definitions, behavioral priors, and regional cold-start priors."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class MarketArchetype(str, Enum):
    DIRECT_LEISURE = "Direct Leisure"
    RESIDENT_VFR = "Resident / VFR"
    REGIONAL_GCC = "Regional GCC"
    HUB_MEDIATED = "Hub-Mediated"
    HIGHLY_SEASONAL = "Highly Seasonal"
    EMERGING_SPARSE = "Emerging / Sparse"
    DOMESTIC_STAYCATION = "Domestic Staycation"


@dataclass(frozen=True)
class ArchetypeProfile:
    archetype: MarketArchetype
    description: str
    typical_los_range: Tuple[float, float]
    typical_multiplier_range: Tuple[float, float]
    seasonality_profile: str
    load_factor_prior: Tuple[float, float]     # Beta(alpha, beta)
    p2p_share_prior: Tuple[float, float]       # Beta(alpha, beta)
    default_los: float
    default_multiplier: float
    default_load_factor: float
    default_p2p_share: float


ARCHETYPE_PROFILES: Dict[MarketArchetype, ArchetypeProfile] = {
    MarketArchetype.DIRECT_LEISURE: ArchetypeProfile(
        archetype=MarketArchetype.DIRECT_LEISURE,
        description="High hotel capture rate, extended vacation stays, strong winter demand.",
        typical_los_range=(4.5, 5.2),
        typical_multiplier_range=(0.85, 1.50),
        seasonality_profile="Winter peak (Nov-Apr), summer trough (Jul-Aug).",
        load_factor_prior=(18.0, 2.5),   # ~88% LF
        p2p_share_prior=(8.0, 14.0),     # ~36% P2P share (rest transfer)
        default_los=4.85,
        default_multiplier=1.05,
        default_load_factor=0.88,
        default_p2p_share=0.36,
    ),
    MarketArchetype.RESIDENT_VFR: ArchetypeProfile(
        archetype=MarketArchetype.RESIDENT_VFR,
        description="High volume P2P traffic, substantial resident/diaspora stays with family, lower hotel conversion.",
        typical_los_range=(3.0, 5.0),
        typical_multiplier_range=(0.10, 0.20),
        seasonality_profile="Steady year-round with Diwali/holiday travel spikes.",
        load_factor_prior=(22.0, 2.5),   # ~90% LF
        p2p_share_prior=(16.0, 10.0),    # ~62% P2P share
        default_los=3.50,
        default_multiplier=0.17,
        default_load_factor=0.89,
        default_p2p_share=0.62,
    ),
    MarketArchetype.REGIONAL_GCC: ArchetypeProfile(
        archetype=MarketArchetype.REGIONAL_GCC,
        description="Short-haul neighbor markets, shorter stays, strong weekend and summer indoor break demand.",
        typical_los_range=(1.6, 3.3),
        typical_multiplier_range=(0.30, 0.70),
        seasonality_profile="High summer holiday, Eid breaks, and weekend elasticity.",
        load_factor_prior=(14.0, 6.0),   # ~70% LF
        p2p_share_prior=(14.0, 10.0),    # ~58% P2P share
        default_los=2.45,
        default_multiplier=0.45,
        default_load_factor=0.72,
        default_p2p_share=0.55,
    ),
    MarketArchetype.HUB_MEDIATED: ArchetypeProfile(
        archetype=MarketArchetype.HUB_MEDIATED,
        description="Substantial visitor volume entering via connecting transfer routes or regional gateway hubs.",
        typical_los_range=(2.1, 4.0),
        typical_multiplier_range=(1.80, 6.50),
        seasonality_profile="Tied to school holidays, Golden Week, spring/autumn travel.",
        load_factor_prior=(15.0, 5.0),   # ~75% LF
        p2p_share_prior=(10.0, 10.0),    # ~50% P2P share
        default_los=3.20,
        default_multiplier=2.20,
        default_load_factor=0.78,
        default_p2p_share=0.48,
    ),
    MarketArchetype.HIGHLY_SEASONAL: ArchetypeProfile(
        archetype=MarketArchetype.HIGHLY_SEASONAL,
        description="Extreme winter sun preference with dramatic summer drawdowns.",
        typical_los_range=(3.8, 5.0),
        typical_multiplier_range=(0.40, 0.85),
        seasonality_profile="High amplitude winter surge, low summer floor.",
        load_factor_prior=(16.0, 3.5),   # ~82% LF
        p2p_share_prior=(14.0, 8.0),     # ~64% P2P share
        default_los=4.40,
        default_multiplier=0.65,
        default_load_factor=0.83,
        default_p2p_share=0.60,
    ),
    MarketArchetype.EMERGING_SPARSE: ArchetypeProfile(
        archetype=MarketArchetype.EMERGING_SPARSE,
        description="Developing routes or pooled smaller international source markets with regularized shrinkage.",
        typical_los_range=(3.0, 4.5),
        typical_multiplier_range=(0.30, 0.80),
        seasonality_profile="Moderate seasonality, sensitive to route introduction.",
        load_factor_prior=(15.0, 5.0),   # ~75% LF
        p2p_share_prior=(12.0, 8.0),     # ~60% P2P share
        default_los=3.50,
        default_multiplier=0.42,
        default_load_factor=0.78,
        default_p2p_share=0.55,
    ),
    MarketArchetype.DOMESTIC_STAYCATION: ArchetypeProfile(
        archetype=MarketArchetype.DOMESTIC_STAYCATION,
        description="Local UAE residents and intra-emirate staycations, weekend trips, and corporate events.",
        typical_los_range=(2.1, 2.5),
        typical_multiplier_range=(1.0, 1.0),
        seasonality_profile="Weekend peaks, public holiday long weekends, school breaks.",
        load_factor_prior=(15.0, 5.0),
        p2p_share_prior=(15.0, 5.0),
        default_los=2.35,
        default_multiplier=1.00,
        default_load_factor=0.75,
        default_p2p_share=1.00,
    ),
}

# Empirical top-15 classification
MARKET_ARCHETYPE_MAP: Dict[str, MarketArchetype] = {
    "INDIA": MarketArchetype.RESIDENT_VFR,
    "RUSSIAN FEDERATION": MarketArchetype.DIRECT_LEISURE,
    "UNITED KINGDOM": MarketArchetype.DIRECT_LEISURE,
    "CHINA": MarketArchetype.HUB_MEDIATED,
    "GERMANY": MarketArchetype.DIRECT_LEISURE,
    "SAUDI ARABIA": MarketArchetype.REGIONAL_GCC,
    "UNITED STATES OF AMERICA": MarketArchetype.HUB_MEDIATED,
    "KUWAIT": MarketArchetype.REGIONAL_GCC,
    "FRANCE": MarketArchetype.DIRECT_LEISURE,
    "EGYPT": MarketArchetype.RESIDENT_VFR,
    "ITALY": MarketArchetype.DIRECT_LEISURE,
    "KAZAKHSTAN": MarketArchetype.HIGHLY_SEASONAL,
    "ISRAEL": MarketArchetype.DIRECT_LEISURE,
    "PHILIPPINES": MarketArchetype.RESIDENT_VFR,
    "OMAN": MarketArchetype.REGIONAL_GCC,
    # FIX (P0-D): Register the 5 regional cluster labels produced by the new panel builder.
    # The old monolithic 'OTHER INTERNATIONAL' is kept for backward compat with existing PKL models.
    "OTHER INTERNATIONAL": MarketArchetype.EMERGING_SPARSE,   # legacy — deprecated
    "OTHER_INTERNATIONAL": MarketArchetype.EMERGING_SPARSE,   # catch-all for unresolved residuals
    "OTHER_EUROPE": MarketArchetype.DIRECT_LEISURE,           # Nordic/Western EU leisure markets
    "OTHER_ASIA_PACIFIC": MarketArchetype.HUB_MEDIATED,       # South Korea, Australia, Japan, Pakistan
    "OTHER_MENA": MarketArchetype.REGIONAL_GCC,               # Jordan, Bahrain, Qatar, Lebanon
    "OTHER_AMERICAS_AFRICA": MarketArchetype.HUB_MEDIATED,    # Canada, Brazil, South Africa, Mexico, Morocco
    "OTHER_EURASIA": MarketArchetype.HIGHLY_SEASONAL,         # Uzbekistan, Azerbaijan, Armenia
    "DOMESTIC": MarketArchetype.DOMESTIC_STAYCATION,
}

# Empirical Top-15 International Markets ranked strictly by verified training guest volume
# Rank 14 is PHILIPPINES (417,156 guests); Rank 18 is ARMENIA (370,463 guests)
TOP_15_INTERNATIONAL_MARKETS = [
    "INDIA",
    "UNITED KINGDOM",
    "RUSSIAN FEDERATION",
    "UNITED STATES OF AMERICA",
    "GERMANY",
    "CHINA",
    "SAUDI ARABIA",
    "FRANCE",
    "EGYPT",
    "KUWAIT",
    "ITALY",
    "KAZAKHSTAN",
    "ISRAEL",
    "PHILIPPINES",
    "OMAN",
]

# Regional clusters to decompose the 30 nationalities pooled in "OTHER INTERNATIONAL" (25.9% of demand)
REGIONAL_CLUSTERS: Dict[str, List[str]] = {
    "OTHER_EUROPE": [
        "POLAND", "NETHERLANDS", "SPAIN", "SWITZERLAND", "AUSTRIA",
        "SWEDEN", "NORWAY", "DENMARK", "FINLAND", "CZECHIA", "ROMANIA",
        "BELGIUM", "IRELAND",
    ],
    "OTHER_ASIA_PACIFIC": [
        "SOUTH KOREA", "AUSTRALIA", "PAKISTAN", "BANGLADESH", "JAPAN",
    ],
    "OTHER_MENA": [
        "JORDAN", "BAHRAIN", "QATAR", "LEBANON",
    ],
    "OTHER_AMERICAS_AFRICA": [
        "CANADA", "BRAZIL", "SOUTH AFRICA", "MEXICO", "MOROCCO",
    ],
    "OTHER_EURASIA": [
        "UZBEKISTAN", "AZERBAIJAN", "ARMENIA",
    ],
}

# Regional cold-start priors for new routes from unmodeled countries
COUNTRY_TO_REGION_MAP: Dict[str, MarketArchetype] = {
    # Scandinavia / Western Europe
    "SWEDEN": MarketArchetype.DIRECT_LEISURE,
    "NORWAY": MarketArchetype.DIRECT_LEISURE,
    "DENMARK": MarketArchetype.DIRECT_LEISURE,
    "FINLAND": MarketArchetype.DIRECT_LEISURE,
    "NETHERLANDS": MarketArchetype.DIRECT_LEISURE,
    "BELGIUM": MarketArchetype.DIRECT_LEISURE,
    "SWITZERLAND": MarketArchetype.DIRECT_LEISURE,
    "AUSTRIA": MarketArchetype.DIRECT_LEISURE,
    "SPAIN": MarketArchetype.DIRECT_LEISURE,
    "IRELAND": MarketArchetype.DIRECT_LEISURE,
    # GCC / Middle East
    "BAHRAIN": MarketArchetype.REGIONAL_GCC,
    "QATAR": MarketArchetype.REGIONAL_GCC,
    "JORDAN": MarketArchetype.REGIONAL_GCC,
    "LEBANON": MarketArchetype.REGIONAL_GCC,
    # South Asia
    "PAKISTAN": MarketArchetype.RESIDENT_VFR,
    "BANGLADESH": MarketArchetype.RESIDENT_VFR,
    # Central / Eastern Europe, Caucasus & CIS
    "ARMENIA": MarketArchetype.HIGHLY_SEASONAL,
    "POLAND": MarketArchetype.HIGHLY_SEASONAL,
    "CZECHIA": MarketArchetype.HIGHLY_SEASONAL,
    "AZERBAIJAN": MarketArchetype.HIGHLY_SEASONAL,
    "UZBEKISTAN": MarketArchetype.HIGHLY_SEASONAL,
    "ROMANIA": MarketArchetype.HIGHLY_SEASONAL,
    # Long-Haul
    "AUSTRALIA": MarketArchetype.HUB_MEDIATED,
    "CANADA": MarketArchetype.HUB_MEDIATED,
    "JAPAN": MarketArchetype.HUB_MEDIATED,
    "SOUTH KOREA": MarketArchetype.HUB_MEDIATED,
    "BRAZIL": MarketArchetype.HUB_MEDIATED,
    "SOUTH AFRICA": MarketArchetype.HUB_MEDIATED,
    "MEXICO": MarketArchetype.HUB_MEDIATED,
    "MOROCCO": MarketArchetype.REGIONAL_GCC,
}


def get_market_archetype(market_name: str) -> MarketArchetype:
    """Return archetype for a market, using direct map, regional map, or EMERGING_SPARSE."""
    norm = market_name.upper().strip()
    if norm in MARKET_ARCHETYPE_MAP:
        return MARKET_ARCHETYPE_MAP[norm]
    if norm in COUNTRY_TO_REGION_MAP:
        return COUNTRY_TO_REGION_MAP[norm]
    return MarketArchetype.EMERGING_SPARSE


def get_archetype_profile(archetype: MarketArchetype) -> ArchetypeProfile:
    """Return the profile for a given archetype."""
    return ARCHETYPE_PROFILES[archetype]


def get_cold_start_prior(country_name: str) -> ArchetypeProfile:
    """Return cold-start profile for an unmodeled country via hierarchical regional shrinkage."""
    arch = get_market_archetype(country_name)
    return ARCHETYPE_PROFILES[arch]
