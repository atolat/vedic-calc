"""Tests for dosha detection."""

import pytest

from vedic_calc import calculate_chart
from vedic_calc.core.constants import Planet
from vedic_calc.dosha.calculator import detect_doshas


@pytest.fixture
def mumbai_chart():
    return calculate_chart(
        year=1990, month=3, day=15, hour=10, minute=30,
        latitude=19.0760, longitude=72.8777, timezone_offset=5.5,
    )


class TestDoshaStructure:
    def test_returns_list(self, mumbai_chart):
        doshas = detect_doshas(mumbai_chart)
        assert isinstance(doshas, list)
        assert len(doshas) > 0

    def test_dosha_has_required_fields(self, mumbai_chart):
        doshas = detect_doshas(mumbai_chart)
        for d in doshas:
            assert hasattr(d, "name")
            assert hasattr(d, "is_present")
            assert hasattr(d, "severity")
            assert hasattr(d, "cancellation_factors")
            assert hasattr(d, "description")

    def test_severity_valid(self, mumbai_chart):
        doshas = detect_doshas(mumbai_chart)
        valid_severities = {"none", "mild", "moderate", "severe"}
        for d in doshas:
            assert d.severity in valid_severities, f"{d.name}: invalid severity '{d.severity}'"


class TestDoshaTypes:
    def test_manglik_checked(self, mumbai_chart):
        doshas = detect_doshas(mumbai_chart)
        manglik = [d for d in doshas if "Manglik" in d.name or "Kuja" in d.name]
        assert len(manglik) >= 1

    def test_kaal_sarpa_checked(self, mumbai_chart):
        doshas = detect_doshas(mumbai_chart)
        ks = [d for d in doshas if "Kaal Sarpa" in d.name]
        assert len(ks) >= 1

    def test_not_present_has_none_severity(self, mumbai_chart):
        doshas = detect_doshas(mumbai_chart)
        for d in doshas:
            if not d.is_present:
                assert d.severity == "none"
