"""Event Timeline — chronological life events derived from a birth chart.

Collects major astrological events (dasha transitions, Sade Sati phases,
Saturn returns, Jupiter transits over Moon, Rahu-Ketu returns) into a
single sorted timeline for a given date range.

This is useful for giving a bird's-eye view of someone's life themes
across decades — which planetary periods were active, when major transits
hit, etc.
"""

from __future__ import annotations

from datetime import datetime

from vedic_calc.core.constants import Ayanamsa, Planet, Sign, PLANET_NAMES, SIGN_NAMES
from vedic_calc.core.ephemeris import _to_julian_day, jd_to_datetime, get_planet_longitude
from vedic_calc.core.search import find_sign_entry
from vedic_calc.core.types import BirthChart, EventTimeline, TimelineEvent
from vedic_calc.dasha.calculator import calculate_dasha
from vedic_calc.chart.sade_sati import calculate_sade_sati_periods


def _dt_to_jd(dt: datetime, tz_offset: float) -> float:
    """Convert a datetime to Julian Day, adjusting for timezone."""
    return _to_julian_day(
        dt.year, dt.month, dt.day,
        dt.hour + dt.minute / 60.0 - tz_offset,
    )


def _planet_name(planet: Planet) -> str:
    """Short English name for a planet (without the Sanskrit parenthetical)."""
    return PLANET_NAMES[planet].split(" (")[0]


def _sign_name(sign: Sign) -> str:
    """Short English name for a sign (without the Sanskrit parenthetical)."""
    return SIGN_NAMES[sign].split(" (")[0]


def _in_range(dt: datetime, start: datetime, end: datetime) -> bool:
    """Check if a datetime falls within [start, end)."""
    return start <= dt < end


def _collect_dasha_transitions(
    chart: BirthChart,
    start_date: datetime,
    end_date: datetime,
) -> list[TimelineEvent]:
    """Collect mahadasha transition events within the date range."""
    events: list[TimelineEvent] = []
    mahadashas = [p for p in calculate_dasha(chart, levels=1) if p.level == "mahadasha"]

    for i, period in enumerate(mahadashas):
        if not _in_range(period.start, start_date, end_date):
            continue

        # Determine the "from" dasha (previous mahadasha)
        if i > 0:
            from_lord = _planet_name(mahadashas[i - 1].lord)
        else:
            from_lord = "—"

        to_lord = _planet_name(period.lord)
        events.append(TimelineEvent(
            event_type="dasha_transition",
            date=period.start,
            description=f"Mahadasha transition: {from_lord} → {to_lord}",
            details={"from": from_lord, "to": to_lord},
        ))

    return events


def _collect_sade_sati_events(
    chart: BirthChart,
    start_date: datetime,
    end_date: datetime,
    ayanamsa: Ayanamsa,
) -> list[TimelineEvent]:
    """Collect Sade Sati start/end events within the date range."""
    events: list[TimelineEvent] = []
    result = calculate_sade_sati_periods(chart, start_date, end_date, ayanamsa)

    for phase in result.phases:
        sign_label = _sign_name(phase.sign)
        phase_label = phase.phase  # "rising", "peak", "setting"

        if _in_range(phase.start, start_date, end_date):
            events.append(TimelineEvent(
                event_type="sade_sati_start",
                date=phase.start,
                description=f"Sade Sati {phase_label} phase begins (Saturn in {sign_label})",
                details={"phase": phase_label, "sign": sign_label},
            ))

        if _in_range(phase.end, start_date, end_date):
            events.append(TimelineEvent(
                event_type="sade_sati_end",
                date=phase.end,
                description=f"Sade Sati {phase_label} phase ends (Saturn leaves {sign_label})",
                details={"phase": phase_label, "sign": sign_label},
            ))

    return events


def _collect_saturn_returns(
    chart: BirthChart,
    start_date: datetime,
    end_date: datetime,
    ayanamsa: Ayanamsa,
) -> list[TimelineEvent]:
    """Find Saturn return events (Saturn returning to natal sign, ~29.5 yr cycle)."""
    events: list[TimelineEvent] = []
    natal_saturn_sign = chart.planets[Planet.SATURN].sign
    natal_sign_num = int(natal_saturn_sign)
    sign_label = _sign_name(natal_saturn_sign)
    tz = chart.timezone_offset

    birth_year = chart.birth_datetime.year

    # Search around expected return times: birth + 29.5, +59, +88.5 years
    for offset_years in (29.5, 59.0, 88.5):
        expected_year = birth_year + offset_years
        # Build a 2-year search window centered on expected return
        window_start_year = int(expected_year - 1)
        window_end_year = int(expected_year + 1)

        window_start = datetime(window_start_year, 1, 1)
        window_end = datetime(window_end_year, 12, 31, 23, 59)

        # Clamp to requested range
        ws = max(window_start, start_date)
        we = min(window_end, end_date)
        if ws >= we:
            continue

        jd_start = _dt_to_jd(ws, tz)
        jd_end = _dt_to_jd(we, tz)

        entry_jd = find_sign_entry(Planet.SATURN, natal_sign_num, jd_start, jd_end, ayanamsa)
        if entry_jd is not None:
            dt = jd_to_datetime(entry_jd, tz)
            if _in_range(dt, start_date, end_date):
                return_num = int(round(offset_years / 29.5))
                ordinal = {1: "1st", 2: "2nd", 3: "3rd"}.get(return_num, f"{return_num}th")
                events.append(TimelineEvent(
                    event_type="saturn_return",
                    date=dt,
                    description=f"{ordinal} Saturn return — Saturn enters natal {sign_label}",
                    details={"return_number": str(return_num), "sign": sign_label},
                ))

    return events


def _collect_jupiter_transits(
    chart: BirthChart,
    start_date: datetime,
    end_date: datetime,
    ayanamsa: Ayanamsa,
) -> list[TimelineEvent]:
    """Find when Jupiter transits over natal Moon sign (~12 yr cycle)."""
    events: list[TimelineEvent] = []
    natal_moon_sign = chart.planets[Planet.MOON].sign
    natal_sign_num = int(natal_moon_sign)
    sign_label = _sign_name(natal_moon_sign)
    tz = chart.timezone_offset

    # Jupiter takes ~12 years per cycle. Scan in 1-year windows across the range.
    year = start_date.year
    end_year = end_date.year

    while year <= end_year:
        ws = max(datetime(year, 1, 1), start_date)
        we = min(datetime(year, 12, 31, 23, 59), end_date)
        if ws >= we:
            year += 1
            continue

        jd_start = _dt_to_jd(ws, tz)
        jd_end = _dt_to_jd(we, tz)

        entry_jd = find_sign_entry(Planet.JUPITER, natal_sign_num, jd_start, jd_end, ayanamsa)
        if entry_jd is not None:
            dt = jd_to_datetime(entry_jd, tz)
            if _in_range(dt, start_date, end_date):
                events.append(TimelineEvent(
                    event_type="jupiter_transit",
                    date=dt,
                    description=f"Jupiter enters natal Moon sign {sign_label}",
                    details={"sign": sign_label},
                ))

        year += 1

    return events


def _collect_rahu_ketu_returns(
    chart: BirthChart,
    start_date: datetime,
    end_date: datetime,
    ayanamsa: Ayanamsa,
) -> list[TimelineEvent]:
    """Find Rahu-Ketu return events (Rahu returning to natal sign, ~18.6 yr cycle)."""
    events: list[TimelineEvent] = []
    natal_rahu_sign = chart.planets[Planet.RAHU].sign
    natal_sign_num = int(natal_rahu_sign)
    sign_label = _sign_name(natal_rahu_sign)
    tz = chart.timezone_offset

    birth_year = chart.birth_datetime.year

    # Search around expected return times: birth + 18.6, +37.2, +55.8, +74.4, +93 years
    cycle_years = 18.6
    for i in range(1, 7):
        offset_years = cycle_years * i
        expected_year = birth_year + offset_years
        window_start_year = int(expected_year - 1)
        window_end_year = int(expected_year + 1)

        window_start = datetime(window_start_year, 1, 1)
        window_end = datetime(window_end_year, 12, 31, 23, 59)

        ws = max(window_start, start_date)
        we = min(window_end, end_date)
        if ws >= we:
            continue

        jd_start = _dt_to_jd(ws, tz)
        jd_end = _dt_to_jd(we, tz)

        entry_jd = find_sign_entry(Planet.RAHU, natal_sign_num, jd_start, jd_end, ayanamsa)
        if entry_jd is not None:
            dt = jd_to_datetime(entry_jd, tz)
            if _in_range(dt, start_date, end_date):
                ordinal = {1: "1st", 2: "2nd", 3: "3rd"}.get(i, f"{i}th")
                events.append(TimelineEvent(
                    event_type="rahu_ketu_return",
                    date=dt,
                    description=f"{ordinal} Rahu-Ketu return — Rahu enters natal {sign_label}",
                    details={"return_number": str(i), "sign": sign_label},
                ))

    return events


def calculate_event_timeline(
    chart: BirthChart,
    start_date: datetime,
    end_date: datetime,
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI,
) -> EventTimeline:
    """Calculate a chronological timeline of major astrological events.

    Collects dasha transitions, Sade Sati phases, Saturn returns, Jupiter
    transits over natal Moon, and Rahu-Ketu returns into a single sorted
    timeline.

    Args:
        chart: A calculated BirthChart.
        start_date: Start of the timeline range.
        end_date: End of the timeline range.
        ayanamsa: Ayanamsa for transit calculations.

    Returns:
        EventTimeline with all events sorted chronologically.

    Example:
        >>> from vedic_calc.chart.calculator import calculate_chart
        >>> chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
        >>> timeline = calculate_event_timeline(
        ...     chart,
        ...     datetime(1990, 1, 1),
        ...     datetime(2050, 1, 1),
        ... )
        >>> len(timeline.events) > 0
        True
    """
    all_events: list[TimelineEvent] = []

    # 1. Dasha transitions
    all_events.extend(_collect_dasha_transitions(chart, start_date, end_date))

    # 2. Sade Sati phases
    all_events.extend(_collect_sade_sati_events(chart, start_date, end_date, ayanamsa))

    # 3. Saturn returns
    all_events.extend(_collect_saturn_returns(chart, start_date, end_date, ayanamsa))

    # 4. Jupiter transits over natal Moon
    all_events.extend(_collect_jupiter_transits(chart, start_date, end_date, ayanamsa))

    # 5. Rahu-Ketu returns
    all_events.extend(_collect_rahu_ketu_returns(chart, start_date, end_date, ayanamsa))

    # Sort all events chronologically
    all_events.sort(key=lambda e: e.date)

    # Build a label from chart info
    birth = chart.birth_datetime
    label = f"{birth.year}"

    return EventTimeline(
        chart_owner=label,
        start_date=start_date,
        end_date=end_date,
        events=all_events,
    )
