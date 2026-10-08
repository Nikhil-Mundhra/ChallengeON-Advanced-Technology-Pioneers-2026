"""The modeled market universe: individually modeled source markets and the regional clusters
that pool the remaining nationalities."""

from __future__ import annotations

from typing import Dict, List

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
        "UZBEKISTAN", "AZERBAIJAN", "ARMENIA", "TURKEY",
    ],
}
