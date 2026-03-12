"""Fixtures and utilities for PyJHora comparison tests.

This module provides:
- Index mapping between vedic-calc and PyJHora conventions
- Reference chart fixtures for consistent testing
- ComparisonRecord dataclass for collecting test results
- Helper functions to create PyJHora inputs from reference chart data
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pytest

from vedic_calc import calculate_chart
from vedic_calc.core.constants import Ayanamsa, Planet, Sign


# ---------------------------------------------------------------------------
# Index mapping: vedic-calc ↔ PyJHora
# ---------------------------------------------------------------------------
# vedic-calc: Sun=0, Moon=1, Mars=2, Mercury=3, Jupiter=4, Venus=5, Saturn=6, Rahu=7, Ketu=8
# PyJHora:    Sun=0, Moon=1, Mercury=2, Venus=3, Mars=4, Jupiter=5, Saturn=6, Rahu=11, Ketu=-10

# Map vedic-calc Planet enum value → PyJHora planet constant
VC_TO_PJ_PLANET = {
    0: 0,    # Sun → Sun
    1: 1,    # Moon → Moon
    2: 4,    # Mars → Mars (PyJHora _MARS=4)
    3: 2,    # Mercury → Mercury (PyJHora _MERCURY=2)
    4: 5,    # Jupiter → Jupiter (PyJHora _JUPITER=5)
    5: 3,    # Venus → Venus (PyJHora _VENUS=3)
    6: 6,    # Saturn → Saturn
    7: 11,   # Rahu → Rahu (PyJHora _RAHU=11)
    8: -10,  # Ketu → Ketu (PyJHora _KETU=-10)
}

PJ_TO_VC_PLANET = {v: k for k, v in VC_TO_PJ_PLANET.items()}

# PyJHora dhasavarga returns planet indices 0-8 sequentially.
# Verified by comparing D1 output with direct sidereal longitudes:
# The order is: Sun=0, Moon=1, Mars=2, Mercury=3, Jupiter=4, Venus=5, Saturn=6, Rahu=7, Ketu=8
# This is the SAME as vedic-calc's Planet enum, so the mapping is identity.
# Plus Lagna=9, Uranus=10, Neptune=11 (which we skip).
PJ_DHASA_TO_VC_PLANET = {
    0: 0,  # Sun → Sun
    1: 1,  # Moon → Moon
    2: 2,  # Mars → Mars
    3: 3,  # Mercury → Mercury
    4: 4,  # Jupiter → Jupiter
    5: 5,  # Venus → Venus
    6: 6,  # Saturn → Saturn
    7: 7,  # Rahu → Rahu
    8: 8,  # Ketu → Ketu
}

# Sign mapping: vedic-calc uses 1-12, PyJHora uses 0-11
def map_pj_sign_to_vc(pj_sign: int) -> int:
    """Convert PyJHora sign (0-11) to vedic-calc Sign (1-12)."""
    return pj_sign + 1


def map_vc_sign_to_pj(vc_sign: int) -> int:
    """Convert vedic-calc Sign (1-12) to PyJHora sign (0-11)."""
    return vc_sign - 1


# PyJHora dasha lord IDs in Vimsottari/Yogini/Ashtottari output:
# Verified by matching period durations to known dasha cycles.
# E.g., lord_id=7 has 18yr period = Rahu, lord_id=4 has 16yr = Jupiter.
# Order: Sun=0, Moon=1, Mars=2, Mercury=3, Jupiter=4, Venus=5, Saturn=6, Rahu=7, Ketu=8
# Same as vedic-calc and same as dhasavarga — identity mapping.
PJ_DASHA_LORD_TO_VC = PJ_DHASA_TO_VC_PLANET


# ---------------------------------------------------------------------------
# PyJHora helper: create inputs from reference chart data
# ---------------------------------------------------------------------------

def pj_setup(ref: "ReferenceChart"):
    """Set up PyJHora and return (jd, place, dob, tob) for a reference chart."""
    from jhora.panchanga import drik
    from jhora import utils

    drik.set_ayanamsa_mode("LAHIRI")
    place = drik.Place(
        ref.label, ref.latitude, ref.longitude, ref.timezone_offset
    )
    dob = drik.Date(ref.year, ref.month, ref.day)
    tob = (ref.hour, ref.minute, 0)
    jd = utils.julian_day_number(dob, tob)
    return jd, place, dob, tob


def pj_build_chart_1d(jd, place):
    """Build PyJHora chart_1d (list of 12 strings) from planet positions.

    Uses PyJHora's own dhasavarga() to compute D1 planet positions, ensuring
    planet sign placements and planet ID numbering are identical to what
    PyJHora uses internally.  dhasavarga() handles JD local-to-UTC conversion.

    Planet IDs in the returned chart_1d follow PyJHora's dhasavarga indexing:
    0=Sun, 1=Moon, 2=Mars, 3=Mercury, 4=Jupiter, 5=Venus, 6=Saturn, 7=Rahu, 8=Ketu.
    'L' marks the ascendant (Lagna).

    IMPORTANT: We build chart_1d manually from dhasavarga output, including
    only planets 0-8 (not Lagna=9, Uranus=10, Neptune=11).  PyJHora's
    get_planet_to_house_dict_from_chart uses substring matching (``str(p) in s``)
    which causes planet 0 to match '10' and planet 1 to match '10'/'11',
    corrupting the position dict when multi-digit IDs are present.
    """
    from jhora.panchanga import drik

    # dhasavarga returns [(pid, (sign, deg)), ...] for planets 0-11
    # We only use 0-8 (Sun-Ketu) to avoid multi-digit ID parsing issues.
    d1 = drik.dhasavarga(jd, place, 1)

    # Build chart_1d manually: 12 sign slots, only planets 0-8
    chart_1d = [""] * 12
    for pid, (sign, _deg) in d1:
        if pid > 8:  # Skip Lagna(9), Uranus(10), Neptune(11)
            continue
        if chart_1d[sign]:
            chart_1d[sign] += "/" + str(pid)
        else:
            chart_1d[sign] = str(pid)

    # Add ascendant
    asc = drik.ascendant(jd, place)
    asc_sign = asc[0]
    if chart_1d[asc_sign]:
        chart_1d[asc_sign] = "L/" + chart_1d[asc_sign]
    else:
        chart_1d[asc_sign] = "L"

    return chart_1d


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

    report_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports"
    )
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
    total_pass = sum(c["pass"] for c in summary.values())
    total_fail = sum(c["fail"] for c in summary.values())
    total_all = sum(c["total"] for c in summary.values())

    lines = [
        "# vedic-calc vs PyJHora Comparison Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"**Overall: {total_pass}/{total_all} checks passed"
        f" ({total_pass / total_all * 100:.0f}%)**" if total_all > 0 else "",
        "",
        "## Summary",
        "",
        "| Feature | Checks | Pass | Fail | Pass Rate |",
        "|---------|--------|------|------|-----------|",
    ]
    for feature, counts in summary.items():
        rate = (
            f"{counts['pass'] / counts['total'] * 100:.0f}%"
            if counts["total"] > 0
            else "N/A"
        )
        lines.append(
            f"| {feature} | {counts['total']} | {counts['pass']}"
            f" | {counts['fail']} | {rate} |"
        )

    lines.extend(["", "## Detailed Results", ""])
    current_feature = None
    for r in _collector.records:
        if r.feature != current_feature:
            current_feature = r.feature
            lines.append(f"### {current_feature}")
            lines.append("")
        status = "PASS" if r.match else "**FAIL**"
        lines.append(
            f"- {status} | {r.chart_label} | "
            f"vc=`{r.vedic_calc_result}` | pj=`{r.pyjhora_result}`"
            + (f" | {r.notes}" if r.notes else "")
        )
    lines.append("")

    with open(os.path.join(report_dir, "comparison_report.md"), "w") as f:
        f.write("\n".join(lines))
