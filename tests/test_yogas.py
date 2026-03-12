"""Tests for yoga detection."""

import pytest

from vedic_calc import calculate_chart
from vedic_calc.core.constants import Planet, Sign
from vedic_calc.yoga.calculator import detect_yogas


@pytest.fixture
def mumbai_chart():
    return calculate_chart(
        year=1990, month=3, day=15, hour=10, minute=30,
        latitude=19.0760, longitude=72.8777, timezone_offset=5.5,
    )


@pytest.fixture
def delhi_chart():
    return calculate_chart(
        year=1985, month=7, day=22, hour=5, minute=15,
        latitude=28.6139, longitude=77.2090, timezone_offset=5.5,
    )


class TestYogaStructure:
    def test_returns_list(self, mumbai_chart):
        yogas = detect_yogas(mumbai_chart)
        assert isinstance(yogas, list)
        assert len(yogas) > 0

    def test_yoga_has_required_fields(self, mumbai_chart):
        yogas = detect_yogas(mumbai_chart)
        for y in yogas:
            assert hasattr(y, "name")
            assert hasattr(y, "category")
            assert hasattr(y, "involved_planets")
            assert hasattr(y, "description")
            assert hasattr(y, "is_present")
            assert isinstance(y.involved_planets, list)

    def test_has_pancha_mahapurusha_checks(self, mumbai_chart):
        """Should check all 5 Pancha Mahapurusha yogas."""
        yogas = detect_yogas(mumbai_chart)
        names = {y.name for y in yogas}
        for name in ["Ruchaka", "Bhadra", "Hamsa", "Malavya", "Shasha"]:
            assert name in names, f"Missing Pancha Mahapurusha yoga: {name}"


class TestYogaDetection:
    def test_gajakesari_check(self, mumbai_chart):
        yogas = detect_yogas(mumbai_chart)
        gk = [y for y in yogas if y.name == "Gajakesari"]
        assert len(gk) == 1

    def test_budhaditya_check(self, mumbai_chart):
        yogas = detect_yogas(mumbai_chart)
        ba = [y for y in yogas if y.name == "Budhaditya"]
        assert len(ba) == 1

    def test_different_charts_may_differ(self, mumbai_chart, delhi_chart):
        y1 = detect_yogas(mumbai_chart)
        y2 = detect_yogas(delhi_chart)
        present1 = {y.name for y in y1 if y.is_present}
        present2 = {y.name for y in y2 if y.is_present}
        # Charts likely differ in some yogas
        # This is just a sanity check — both should run without error
        assert len(y1) > 0
        assert len(y2) > 0
