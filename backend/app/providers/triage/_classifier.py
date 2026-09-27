"""Shared deterministic keyword classifier used by RuleBasedTriage and
SimulatedTriage. Not a TriageProvider itself — just the reusable heuristic
both deterministic providers are built on.
"""

import re

from app.domain.enums import Category, Priority

CATEGORY_KEYWORDS: dict[Category, tuple[str, ...]] = {
    Category.WATER: (
        "water",
        "pipe",
        "pipeline",
        "leak",
        "leakage",
        "burst",
        "tanker",
        "tap",
        "supply line",
        "sewage line",
        "paani",
    ),
    Category.ELECTRICITY: (
        "electric",
        "electricity",
        "power cut",
        "power outage",
        "transformer",
        "voltage",
        "wire",
        "wiring",
        "bijli",
        "meter box",
        "shock",
    ),
    Category.SANITATION: (
        "garbage",
        "trash",
        "waste",
        "sewage",
        "sewer",
        "drain",
        "drainage",
        "gutter",
        "overflow",
        "kachra",
        "nala",
    ),
    Category.STREETLIGHTS: (
        "streetlight",
        "street light",
        "street lamp",
        "lamp post",
        "light pole",
        "pole light",
    ),
    Category.ROADS: (
        "road",
        "pothole",
        "potholes",
        "footpath",
        "pavement",
        "street ",
        "traffic",
        "speed breaker",
        "sadak",
    ),
}

HIGH_PRIORITY_KEYWORDS = (
    "urgent",
    "emergency",
    "danger",
    "dangerous",
    "flooding",
    "flood",
    "fire",
    "accident",
    "collapse",
    "collapsed",
    "burst",
    "shock",
    "child",
    "children",
    "since fajr",
    "for a week",
    "for days",
)

LOW_PRIORITY_KEYWORDS = (
    "minor",
    "small",
    "cosmetic",
    "whenever possible",
    "no rush",
    "not urgent",
)


def classify_category(lowered_text: str) -> Category:
    best_category = Category.OTHER
    best_score = 0
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lowered_text)
        if score > best_score:
            best_score = score
            best_category = category
    return best_category


def classify_priority(lowered_text: str) -> Priority:
    if any(kw in lowered_text for kw in HIGH_PRIORITY_KEYWORDS):
        return Priority.HIGH
    if any(kw in lowered_text for kw in LOW_PRIORITY_KEYWORDS):
        return Priority.LOW
    return Priority.NORMAL


def summarize(text: str, location: str) -> str:
    condensed = re.sub(r"\s+", " ", text).strip()
    summary = f"{condensed} (near {location})" if location else condensed
    return summary[:140]
