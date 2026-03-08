"""Tests for the Panchanga (daily calendar) calculator."""

from datetime import datetime

import pytest

from vedic_calc import calculate_panchanga
from vedic_calc.core.constants import Nakshatra
from vedic_calc.core.types import PanchangaInfo


# Mumbai coordinates for all tests
LAT, LON, TZ = 19.076, 72.878, 5.5


# ---------------------------------------------------------------------------
# Structure tests
# ---------------------------------------------------------------------------

class TestPanchangaStructure:
    """Verify the basic structure of panchanga output."""

    def test_returns_panchanga_info(self):
        p = calculate_panchanga(2026, 3, 8, LAT, LON, TZ)
        assert isinstance(p, PanchangaInfo)

    def test_all_fields_populated(self):
        p = calculate_panchanga(2026, 3, 8, LAT, LON, TZ)
        assert p.vara is not None
        assert p.tithi_name is not None
        assert p.yoga_name is not None
        assert p.karana_name is not None
        assert p.nakshatra is not None

    def test_tithi_range(self):
        """Tithi should be between 1 and 30."""
        p = calculate_panchanga(2026, 3, 8, LAT, LON, TZ)
        assert 1 <= p.tithi_number <= 30

    def test_yoga_range(self):
        """Yoga should be between 1 and 27."""
        p = calculate_panchanga(2026, 3, 8, LAT, LON, TZ)
        assert 1 <= p.yoga_number <= 27

    def test_karana_range(self):
        """Karana should be between 1 and 60."""
        p = calculate_panchanga(2026, 3, 8, LAT, LON, TZ)
        assert 1 <= p.karana_number <= 60

    def test_nakshatra_range(self):
        """Nakshatra should be a valid enum (1-27)."""
        p = calculate_panchanga(2026, 3, 8, LAT, LON, TZ)
        assert 1 <= p.nakshatra.value <= 27


# ---------------------------------------------------------------------------
# Weekday tests
# ---------------------------------------------------------------------------

class TestVara:
    """Verify weekday calculation."""

    def test_known_sunday(self):
        """March 8, 2026 is a Sunday."""
        p = calculate_panchanga(2026, 3, 8, LAT, LON, TZ)
        assert "Sunday" in p.vara

    def test_known_monday(self):
        """March 9, 2026 is a Monday."""
        p = calculate_panchanga(2026, 3, 9, LAT, LON, TZ)
        assert "Monday" in p.vara

    def test_known_saturday(self):
        """March 7, 2026 is a Saturday."""
        p = calculate_panchanga(2026, 3, 7, LAT, LON, TZ)
        assert "Saturday" in p.vara


# ---------------------------------------------------------------------------
# Tithi naming tests
# ---------------------------------------------------------------------------

class TestTithiNames:
    """Verify tithi name format."""

    def test_tithi_name_format(self):
        """Tithi name should contain Shukla, Krishna, Purnima, or Amavasya."""
        p = calculate_panchanga(2026, 3, 8, LAT, LON, TZ)
        valid_parts = ["Shukla", "Krishna", "Purnima", "Amavasya"]
        assert any(part in p.tithi_name for part in valid_parts)


# ---------------------------------------------------------------------------
# Sunrise/sunset tests
# ---------------------------------------------------------------------------

class TestSunriseSunset:
    """Verify sunrise/sunset calculations."""

    def test_sunrise_exists(self):
        """Sunrise should be calculated for normal latitudes."""
        p = calculate_panchanga(2026, 3, 8, LAT, LON, TZ)
        assert p.sunrise is not None

    def test_sunset_exists(self):
        """Sunset should be calculated for normal latitudes."""
        p = calculate_panchanga(2026, 3, 8, LAT, LON, TZ)
        assert p.sunset is not None

    def test_sunrise_before_sunset(self):
        """Sunrise should be before sunset."""
        p = calculate_panchanga(2026, 3, 8, LAT, LON, TZ)
        assert p.sunrise < p.sunset

    def test_sunrise_reasonable_hour(self):
        """Sunrise in Mumbai should be between 5 AM and 7 AM local time."""
        p = calculate_panchanga(2026, 3, 8, LAT, LON, TZ)
        assert 5 <= p.sunrise.hour <= 7


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

class TestPanchangaSerialization:
    """Verify JSON serialization works."""

    def test_to_json(self):
        p = calculate_panchanga(2026, 3, 8, LAT, LON, TZ)
        json_str = p.model_dump_json()
        assert "tithi_name" in json_str
        assert "vara" in json_str

    def test_to_dict(self):
        p = calculate_panchanga(2026, 3, 8, LAT, LON, TZ)
        d = p.model_dump()
        assert isinstance(d, dict)
        assert "tithi_number" in d
