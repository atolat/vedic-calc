"""Tests for Ashtakavarga and Shadbala calculations."""

import pytest

from vedic_calc import calculate_chart
from vedic_calc.core.constants import Planet, Sign
from vedic_calc.strength.ashtakavarga import calculate_ashtakavarga
from vedic_calc.strength.shadbala import calculate_shadbala


@pytest.fixture
def mumbai_chart():
    return calculate_chart(
        year=1990, month=3, day=15, hour=10, minute=30,
        latitude=19.0760, longitude=72.8777, timezone_offset=5.5,
    )


class TestAshtakavargaStructure:
    def test_bhinna_has_7_planets(self, mumbai_chart):
        result = calculate_ashtakavarga(mumbai_chart)
        assert len(result.bhinna) == 7  # Sun through Saturn

    def test_bhinna_has_12_signs(self, mumbai_chart):
        result = calculate_ashtakavarga(mumbai_chart)
        for planet, points in result.bhinna.items():
            assert len(points) == 12, f"{planet.name}: expected 12 sign values"

    def test_bhinna_values_range(self, mumbai_chart):
        """Each sign can have 0-8 benefic points per planet."""
        result = calculate_ashtakavarga(mumbai_chart)
        for planet, points in result.bhinna.items():
            for i, p in enumerate(points):
                assert 0 <= p <= 8, f"{planet.name} sign {i+1}: {p} out of range"

    def test_sarva_has_12_values(self, mumbai_chart):
        result = calculate_ashtakavarga(mumbai_chart)
        assert len(result.sarva) == 12

    def test_sarva_values_range(self, mumbai_chart):
        """Sarva totals range 0-56 per sign."""
        result = calculate_ashtakavarga(mumbai_chart)
        for i, total in enumerate(result.sarva):
            assert 0 <= total <= 56, f"Sign {i+1}: sarva={total} out of range"

    def test_sarva_equals_bhinna_sum(self, mumbai_chart):
        """Sarva should equal sum of all Bhinna values per sign."""
        result = calculate_ashtakavarga(mumbai_chart)
        for sign_idx in range(12):
            expected = sum(result.bhinna[p][sign_idx] for p in result.bhinna)
            assert result.sarva[sign_idx] == expected

    def test_total_sarva_reasonable(self, mumbai_chart):
        """Total SAV should be in a reasonable range (typically 337 ± small variation)."""
        result = calculate_ashtakavarga(mumbai_chart)
        total = sum(result.sarva)
        # The exact total depends on the benefic point tables used.
        # Standard is 337, but some tables give slightly different values.
        assert 330 <= total <= 345, f"Total SAV = {total}, expected ~337"


class TestShadbalaStructure:
    def test_returns_7_planets(self, mumbai_chart):
        result = calculate_shadbala(mumbai_chart)
        assert len(result) == 7  # Sun through Saturn

    def test_excludes_nodes(self, mumbai_chart):
        result = calculate_shadbala(mumbai_chart)
        assert Planet.RAHU not in result
        assert Planet.KETU not in result

    def test_all_components_present(self, mumbai_chart):
        result = calculate_shadbala(mumbai_chart)
        for planet, sb in result.items():
            assert hasattr(sb, "sthana_bala")
            assert hasattr(sb, "dig_bala")
            assert hasattr(sb, "kaala_bala")
            assert hasattr(sb, "chesta_bala")
            assert hasattr(sb, "naisargika_bala")
            assert hasattr(sb, "drik_bala")
            assert hasattr(sb, "total")
            assert hasattr(sb, "is_strong")

    def test_total_is_sum(self, mumbai_chart):
        result = calculate_shadbala(mumbai_chart)
        for planet, sb in result.items():
            expected = (sb.sthana_bala + sb.dig_bala + sb.kaala_bala +
                       sb.chesta_bala + sb.naisargika_bala + sb.drik_bala)
            assert abs(sb.total - expected) < 0.01, f"{planet.name}: total mismatch"

    def test_naisargika_bala_positive(self, mumbai_chart):
        result = calculate_shadbala(mumbai_chart)
        for planet, sb in result.items():
            assert sb.naisargika_bala > 0
