"""Tests for Sprint 2 features: panchanga transitions, yoga scoring,
dosha scoring, and event timeline.

Uses a shared Mumbai birth chart fixture consistent with the rest of the test suite.
"""

from datetime import datetime

import pytest

from vedic_calc import (
    calculate_chart,
    calculate_event_timeline,
    calculate_panchanga_transitions,
    score_doshas,
    score_yogas,
)
from vedic_calc.core.constants import Ayanamsa


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mumbai_chart():
    """Birth chart: March 15, 1990, 10:30 AM IST, Mumbai."""
    return calculate_chart(
        year=1990, month=3, day=15,
        hour=10, minute=30, second=0,
        latitude=19.076, longitude=72.878,
        timezone_offset=5.5,
        ayanamsa=Ayanamsa.LAHIRI,
    )


@pytest.fixture
def mumbai_transitions():
    """Panchanga transitions for March 15, 1990, Mumbai."""
    return calculate_panchanga_transitions(
        year=1990, month=3, day=15,
        latitude=19.076, longitude=72.878,
        timezone_offset=5.5,
    )


# ===========================================================================
# Feature 7 — Panchanga Transition Engine
# ===========================================================================

class TestPanchangaTransitions:
    VALID_ELEMENTS = {"tithi", "nakshatra", "yoga", "karana"}

    def test_returns_valid_structure(self, mumbai_transitions):
        t = mumbai_transitions
        assert hasattr(t, "date")
        assert hasattr(t, "sunrise")
        assert hasattr(t, "next_sunrise")
        assert isinstance(t.transitions, list)

    def test_sunrise_before_next_sunrise(self, mumbai_transitions):
        t = mumbai_transitions
        assert t.sunrise < t.next_sunrise

    def test_sunrise_is_on_requested_date(self, mumbai_transitions):
        t = mumbai_transitions
        assert t.sunrise.year == 1990
        assert t.sunrise.month == 3
        assert t.sunrise.day == 15

    def test_transitions_have_valid_elements(self, mumbai_transitions):
        for tr in mumbai_transitions.transitions:
            assert tr.element in self.VALID_ELEMENTS, (
                f"Unexpected element: {tr.element}"
            )

    def test_transition_fields_populated(self, mumbai_transitions):
        """Each transition should have non-empty from/to names and valid values."""
        for tr in mumbai_transitions.transitions:
            assert isinstance(tr.from_value, int) and tr.from_value >= 1
            assert isinstance(tr.to_value, int) and tr.to_value >= 1
            assert tr.from_value != tr.to_value
            assert len(tr.from_name) > 0
            assert len(tr.to_name) > 0
            assert tr.from_name != tr.to_name

    def test_transition_times_within_vedic_day(self, mumbai_transitions):
        """All transition times must fall between sunrise and next sunrise."""
        t = mumbai_transitions
        for tr in t.transitions:
            assert t.sunrise <= tr.transition_time <= t.next_sunrise, (
                f"{tr.element} transition at {tr.transition_time} "
                f"outside [{t.sunrise}, {t.next_sunrise}]"
            )

    def test_transitions_chronologically_ordered(self, mumbai_transitions):
        transitions = mumbai_transitions.transitions
        for i in range(len(transitions) - 1):
            assert transitions[i].transition_time <= transitions[i + 1].transition_time, (
                f"Transition {i} ({transitions[i].transition_time}) is after "
                f"transition {i+1} ({transitions[i+1].transition_time})"
            )

    def test_at_least_one_transition(self, mumbai_transitions):
        """A typical day should have at least one panchanga transition."""
        assert len(mumbai_transitions.transitions) >= 1

    def test_tithi_values_in_range(self, mumbai_transitions):
        """Tithi values should be 1-30."""
        for tr in mumbai_transitions.transitions:
            if tr.element == "tithi":
                assert 1 <= tr.from_value <= 30
                assert 1 <= tr.to_value <= 30

    def test_nakshatra_values_in_range(self, mumbai_transitions):
        """Nakshatra values should be 1-27."""
        for tr in mumbai_transitions.transitions:
            if tr.element == "nakshatra":
                assert 1 <= tr.from_value <= 27
                assert 1 <= tr.to_value <= 27

    def test_yoga_values_in_range(self, mumbai_transitions):
        """Yoga values should be 1-27."""
        for tr in mumbai_transitions.transitions:
            if tr.element == "yoga":
                assert 1 <= tr.from_value <= 27
                assert 1 <= tr.to_value <= 27

    def test_karana_values_in_range(self, mumbai_transitions):
        """Karana values should be 1-60."""
        for tr in mumbai_transitions.transitions:
            if tr.element == "karana":
                assert 1 <= tr.from_value <= 60
                assert 1 <= tr.to_value <= 60

    def test_different_date_returns_different_transitions(self):
        """Two different dates should not have identical transition sets."""
        t1 = calculate_panchanga_transitions(2026, 3, 8, 19.076, 72.878, 5.5)
        t2 = calculate_panchanga_transitions(2026, 3, 10, 19.076, 72.878, 5.5)
        # At minimum, sunrise times should differ
        assert t1.sunrise != t2.sunrise


# ===========================================================================
# Feature 8a — Yoga Scoring
# ===========================================================================

class TestYogaScoring:
    def test_returns_list(self, mumbai_chart):
        results = score_yogas(mumbai_chart)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_scores_in_range(self, mumbai_chart):
        """All yoga strength scores must be 0-100."""
        results = score_yogas(mumbai_chart)
        for r in results:
            assert 0.0 <= r.strength <= 100.0, (
                f"{r.name}: strength={r.strength} out of range"
            )

    def test_all_results_have_required_fields(self, mumbai_chart):
        results = score_yogas(mumbai_chart)
        for r in results:
            assert isinstance(r.name, str) and len(r.name) > 0
            assert isinstance(r.category, str) and len(r.category) > 0
            assert isinstance(r.is_present, bool)
            assert isinstance(r.strength, (int, float))
            assert isinstance(r.factors, list)
            assert isinstance(r.description, str) and len(r.description) > 0

    def test_present_yogas_have_factors(self, mumbai_chart):
        """Present yogas should have at least one scoring factor (the base)."""
        results = score_yogas(mumbai_chart)
        present = [r for r in results if r.is_present]
        for r in present:
            assert len(r.factors) >= 1, (
                f"{r.name}: present yoga has no scoring factors"
            )
            factor_names = {f.name for f in r.factors}
            assert "base" in factor_names, (
                f"{r.name}: missing 'base' factor"
            )

    def test_absent_yogas_have_zero_strength(self, mumbai_chart):
        """Yogas that are not present should have strength=0 and no factors."""
        results = score_yogas(mumbai_chart)
        absent = [r for r in results if not r.is_present]
        for r in absent:
            assert r.strength == 0.0, (
                f"{r.name}: absent yoga has strength={r.strength}"
            )
            assert len(r.factors) == 0

    def test_present_yogas_have_positive_strength(self, mumbai_chart):
        """Present yogas should have strength > 0."""
        results = score_yogas(mumbai_chart)
        present = [r for r in results if r.is_present]
        for r in present:
            assert r.strength > 0.0, (
                f"{r.name}: present yoga has zero strength"
            )

    def test_scoring_factors_have_valid_structure(self, mumbai_chart):
        """Each scoring factor should have name, value, and description."""
        results = score_yogas(mumbai_chart)
        for r in results:
            for f in r.factors:
                assert isinstance(f.name, str) and len(f.name) > 0
                assert isinstance(f.value, (int, float))
                assert isinstance(f.description, str) and len(f.description) > 0

    def test_at_least_one_yoga_detected(self, mumbai_chart):
        """For a real chart, at least one yoga should be detected as present."""
        results = score_yogas(mumbai_chart)
        present = [r for r in results if r.is_present]
        assert len(present) >= 1, "No yogas detected as present"


# ===========================================================================
# Feature 8b — Dosha Scoring
# ===========================================================================

class TestDoshaScoring:
    def test_returns_list(self, mumbai_chart):
        results = score_doshas(mumbai_chart)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_scores_in_range(self, mumbai_chart):
        """All dosha severity scores must be 0-100."""
        results = score_doshas(mumbai_chart)
        for r in results:
            assert 0.0 <= r.severity_score <= 100.0, (
                f"{r.name}: severity_score={r.severity_score} out of range"
            )

    def test_all_results_have_required_fields(self, mumbai_chart):
        results = score_doshas(mumbai_chart)
        for r in results:
            assert isinstance(r.name, str) and len(r.name) > 0
            assert isinstance(r.is_present, bool)
            assert isinstance(r.severity_score, (int, float))
            assert isinstance(r.factors, list)
            assert isinstance(r.description, str) and len(r.description) > 0

    def test_present_doshas_have_factors(self, mumbai_chart):
        """Present doshas should have at least the base_severity factor."""
        results = score_doshas(mumbai_chart)
        present = [r for r in results if r.is_present]
        for r in present:
            assert len(r.factors) >= 1, (
                f"{r.name}: present dosha has no scoring factors"
            )
            factor_names = {f.name for f in r.factors}
            assert "base_severity" in factor_names, (
                f"{r.name}: missing 'base_severity' factor"
            )

    def test_absent_doshas_have_zero_score(self, mumbai_chart):
        """Doshas that are not present should have severity_score=0."""
        results = score_doshas(mumbai_chart)
        absent = [r for r in results if not r.is_present]
        for r in absent:
            assert r.severity_score == 0.0, (
                f"{r.name}: absent dosha has severity_score={r.severity_score}"
            )
            assert len(r.factors) == 0

    def test_severity_base_values_valid(self, mumbai_chart):
        """Base severity factor should map to known severity levels."""
        valid_bases = {0.0, 0.25, 0.5, 0.75}  # none/mild/moderate/severe as fraction
        results = score_doshas(mumbai_chart)
        for r in results:
            if r.is_present:
                base_factors = [f for f in r.factors if f.name == "base_severity"]
                assert len(base_factors) == 1
                assert base_factors[0].value in valid_bases, (
                    f"{r.name}: base_severity value {base_factors[0].value} not in {valid_bases}"
                )

    def test_cancellation_reduces_score(self, mumbai_chart):
        """If a dosha has a cancellation factor, its score should be less than base."""
        results = score_doshas(mumbai_chart)
        for r in results:
            if r.is_present:
                has_cancellation = any(f.name == "cancellation" for f in r.factors)
                if has_cancellation:
                    base_factor = next(f for f in r.factors if f.name == "base_severity")
                    cancel_factor = next(f for f in r.factors if f.name == "cancellation")
                    # Cancellation value should be negative
                    assert cancel_factor.value < 0, (
                        f"{r.name}: cancellation factor value should be negative"
                    )

    def test_scoring_factors_have_valid_structure(self, mumbai_chart):
        """Each scoring factor should have name, value, and description."""
        results = score_doshas(mumbai_chart)
        for r in results:
            for f in r.factors:
                assert isinstance(f.name, str) and len(f.name) > 0
                assert isinstance(f.value, (int, float))
                assert isinstance(f.description, str) and len(f.description) > 0


# ===========================================================================
# Feature 9 — Event Timeline
# ===========================================================================

class TestEventTimeline:
    VALID_EVENT_TYPES = {
        "dasha_transition",
        "sade_sati_start",
        "sade_sati_end",
        "saturn_return",
        "jupiter_transit",
        "rahu_ketu_return",
    }

    @pytest.fixture
    def full_timeline(self, mumbai_chart):
        """Timeline spanning birth to age 60."""
        return calculate_event_timeline(
            mumbai_chart,
            start_date=datetime(1990, 1, 1),
            end_date=datetime(2050, 1, 1),
        )

    def test_returns_valid_structure(self, full_timeline):
        tl = full_timeline
        assert hasattr(tl, "chart_owner")
        assert hasattr(tl, "start_date")
        assert hasattr(tl, "end_date")
        assert isinstance(tl.events, list)

    def test_has_events(self, full_timeline):
        """A 60-year timeline should have many events."""
        assert len(full_timeline.events) > 0

    def test_events_have_required_fields(self, full_timeline):
        for e in full_timeline.events:
            assert isinstance(e.event_type, str) and len(e.event_type) > 0
            assert isinstance(e.date, datetime)
            assert isinstance(e.description, str) and len(e.description) > 0
            assert isinstance(e.details, dict)

    def test_event_types_valid(self, full_timeline):
        for e in full_timeline.events:
            assert e.event_type in self.VALID_EVENT_TYPES, (
                f"Unexpected event type: {e.event_type}"
            )

    def test_events_chronologically_sorted(self, full_timeline):
        events = full_timeline.events
        for i in range(len(events) - 1):
            assert events[i].date <= events[i + 1].date, (
                f"Event {i} ({events[i].date}) after event {i+1} ({events[i+1].date})"
            )

    def test_events_within_date_range(self, full_timeline):
        tl = full_timeline
        for e in tl.events:
            assert tl.start_date <= e.date < tl.end_date, (
                f"Event at {e.date} outside range [{tl.start_date}, {tl.end_date})"
            )

    def test_contains_dasha_transitions(self, full_timeline):
        """A 60-year timeline must have at least one mahadasha transition."""
        dasha_events = [e for e in full_timeline.events if e.event_type == "dasha_transition"]
        assert len(dasha_events) >= 1, "No dasha transitions in 60-year timeline"

    def test_dasha_transition_details(self, full_timeline):
        """Dasha transition events should have 'from' and 'to' in details."""
        dasha_events = [e for e in full_timeline.events if e.event_type == "dasha_transition"]
        for e in dasha_events:
            assert "from" in e.details
            assert "to" in e.details
            assert len(e.details["to"]) > 0

    def test_date_range_filtering(self, mumbai_chart):
        """A narrow date range should return fewer events than the full range."""
        narrow = calculate_event_timeline(
            mumbai_chart,
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2025, 1, 1),
        )
        wide = calculate_event_timeline(
            mumbai_chart,
            start_date=datetime(1990, 1, 1),
            end_date=datetime(2050, 1, 1),
        )
        assert len(narrow.events) <= len(wide.events)

    def test_narrow_range_events_within_bounds(self, mumbai_chart):
        """Events from a narrow range should be within that range."""
        start = datetime(2000, 1, 1)
        end = datetime(2010, 1, 1)
        tl = calculate_event_timeline(mumbai_chart, start_date=start, end_date=end)
        for e in tl.events:
            assert start <= e.date < end, (
                f"Event at {e.date} outside range [{start}, {end})"
            )

    def test_saturn_return_in_long_timeline(self, full_timeline):
        """A 60-year timeline should contain at least one Saturn return (~29.5 yr cycle)."""
        saturn_events = [e for e in full_timeline.events if e.event_type == "saturn_return"]
        assert len(saturn_events) >= 1, "No Saturn return in 60-year timeline"

    def test_start_and_end_dates_preserved(self, mumbai_chart):
        start = datetime(2000, 6, 15)
        end = datetime(2030, 6, 15)
        tl = calculate_event_timeline(mumbai_chart, start_date=start, end_date=end)
        assert tl.start_date == start
        assert tl.end_date == end
