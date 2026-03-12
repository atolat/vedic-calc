"""Fixtures and utilities for PyJHora comparison tests.

This module provides:
- Index mapping between vedic-calc and PyJHora conventions
- Reference chart fixtures for consistent testing
- ComparisonRecord dataclass for collecting test results
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import pytest

from vedic_calc import calculate_chart
from vedic_calc.core.constants import Ayanamsa, Planet, Sign


# ---------------------------------------------------------------------------
# Index mapping: vedic-calc ↔ PyJHora
# ---------------------------------------------------------------------------
# vedic-calc: Sun=0, Moon=1, Mars=2, Mercury=3, Jupiter=4, Venus=5, Saturn=6, Rahu=7, Ketu=8
# PyJHora:    Sun=0, Moon=1, Mercury=2, Venus=3, Mars=4, Jupiter=5, Saturn=6, Rahu=7, Ketu=8

PYJHORA_TO_VC_PLANET: dict[int, int] = {
    0: 0,  # Sun → Sun
    1: 1,  # Moon → Moon
    2: 3,  # Mercury → Mercury
    3: 5,  # Venus → Venus (PyJHora 3=Venus, vc 5=Venus)
    4: 2,  # Mars → Mars (PyJHora 4=Mars, vc 2=Mars)
    5: 4,  # Jupiter → Jupiter (PyJHora 5=Jupiter, vc 4=Jupiter... wait, same)
    6: 6,  # Saturn → Saturn
    7: 7,  # Rahu → Rahu
    8: 8,  # Ketu → Ketu
}

VC_TO_PYJHORA_PLANET: dict[int, int] = {v: k for k, v in PYJHORA_TO_VC_PLANET.items()}

# Sign mapping: vedic-calc uses 1-12, PyJHora uses 0-11
def map_pj_sign(pj_sign: int) -> int:
    """Convert PyJHora sign (0-11) to vedic-calc Sign (1-12)."""
    return pj_sign + 1


def map_vc_sign(vc_sign: int) -> int:
    """Convert vedic-calc Sign (1-12) to PyJHora sign (0-11)."""
    return vc_sign - 1


def map_planet_vc_to_pj(vc_planet: Planet) -> int:
    """Convert vedic-calc Planet to PyJHora planet index."""
    return VC_TO_PYJHORA_PLANET[vc_planet.value]


def map_planet_pj_to_vc(pj_planet: int) -> Planet:
    """Convert PyJHora planet index to vedic-calc Planet."""
    return Planet(PYJHORA_TO_VC_PLANET[pj_planet])


# ---------------------------------------------------------------------------
# Reference charts
# ---------------------------------------------------------------------------

@dataclass
class ReferenceChart:
    """A reference chart used across all comparison tests."""
    label: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    latitude: float
    longitude: float
    timezone_offset: float

    def calculate(self):
        """Calculate the vedic-calc BirthChart."""
        return calculate_chart(
            year=self.year, month=self.month, day=self.day,
            hour=self.hour, minute=self.minute,
            latitude=self.latitude, longitude=self.longitude,
            timezone_offset=self.timezone_offset,
            ayanamsa=Ayanamsa.LAHIRI,
        )


REFERENCE_CHARTS = [
    ReferenceChart(
        label="Chart A (Mumbai 1990)",
        year=1990, month=3, day=15, hour=10, minute=30,
        latitude=19.0760, longitude=72.8777, timezone_offset=5.5,
    ),
    ReferenceChart(
        label="Chart B (Delhi 1985)",
        year=1985, month=7, day=22, hour=5, minute=15,
        latitude=28.6139, longitude=77.2090, timezone_offset=5.5,
    ),
    ReferenceChart(
        label="Chart C (Chennai 2000)",
        year=2000, month=12, day=1, hour=22, minute=45,
        latitude=13.0827, longitude=80.2707, timezone_offset=5.5,
    ),
]


# ---------------------------------------------------------------------------
# Comparison result collection
# ---------------------------------------------------------------------------

@dataclass
class ComparisonRecord:
    """A single comparison data point between vedic-calc and PyJHora."""
    feature: str
    chart_label: str
    vedic_calc_result: Any
    pyjhora_result: Any
    match: bool
    vc_time_ms: float = 0.0
    pj_time_ms: float = 0.0
    tolerance: float = 0.0
    notes: str = ""


class ComparisonCollector:
    """Collects ComparisonRecords during a test session."""

    def __init__(self):
        self.records: list[ComparisonRecord] = []

    def add(self, record: ComparisonRecord) -> None:
        self.records.append(record)

    def summary(self) -> dict[str, dict[str, int]]:
        """Group results by feature."""
        summary: dict[str, dict[str, int]] = {}
        for r in self.records:
            if r.feature not in summary:
                summary[r.feature] = {"pass": 0, "fail": 0, "total": 0}
            summary[r.feature]["total"] += 1
            if r.match:
                summary[r.feature]["pass"] += 1
            else:
                summary[r.feature]["fail"] += 1
        return summary


# Global collector instance
_collector = ComparisonCollector()


@pytest.fixture
def collector():
    """Provide the global comparison collector."""
    return _collector


@pytest.fixture(params=REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS])
def reference_chart(request):
    """Parametrized fixture providing each reference chart."""
    return request.param


@pytest.fixture(params=REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS])
def vc_chart(request):
    """Parametrized fixture providing calculated vedic-calc charts."""
    return request.param.calculate()


def pytest_sessionfinish(session, exitstatus):
    """Generate comparison report at end of test session."""
    if not _collector.records:
        return

    summary = _collector.summary()

    # Only generate report if there are actual comparison results
    import json
    import os
    from datetime import datetime

    report_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports")
    os.makedirs(report_dir, exist_ok=True)

    # JSON report
    json_report = {
        "generated": datetime.now().isoformat(),
        "summary": summary,
        "records": [
            {
                "feature": r.feature,
                "chart": r.chart_label,
                "vc_result": str(r.vedic_calc_result),
                "pj_result": str(r.pyjhora_result),
                "match": r.match,
                "vc_time_ms": r.vc_time_ms,
                "pj_time_ms": r.pj_time_ms,
                "notes": r.notes,
            }
            for r in _collector.records
        ],
    }
    with open(os.path.join(report_dir, "comparison_report.json"), "w") as f:
        json.dump(json_report, f, indent=2)

    # Markdown report
    lines = [
        "# vedic-calc vs PyJHora Comparison Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Summary",
        "| Feature | Charts Tested | Pass | Fail | Pass Rate |",
        "|---------|--------------|------|------|-----------|",
    ]
    for feature, counts in summary.items():
        rate = f"{counts['pass'] / counts['total'] * 100:.0f}%" if counts["total"] > 0 else "N/A"
        lines.append(
            f"| {feature} | {counts['total']} | {counts['pass']} | {counts['fail']} | {rate} |"
        )
    lines.extend(["", "## Detailed Results", ""])
    for r in _collector.records:
        status = "✅" if r.match else "❌"
        lines.append(f"- {status} **{r.feature}** ({r.chart_label}): vc={r.vedic_calc_result}, pj={r.pyjhora_result}")

    with open(os.path.join(report_dir, "comparison_report.md"), "w") as f:
        f.write("\n".join(lines))
