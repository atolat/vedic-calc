"""Tests for Sprint 3 features (10-14): Sookshma/Prana Dasha, KP Significators,
Sudarshana Chakra, Papasamyam, Panchavargeeya Bala, and Mudda Dasha antardashas.

Uses shared Mumbai and Delhi birth chart fixtures.
"""

from datetime import datetime

import pytest

from vedic_calc import (
    calculate_chart,
    calculate_dasha,
    calculate_kp_chart,
    calculate_sudarshana_chakra,
    calculate_papasamyam,
    calculate_panchavargeeya_bala,
    calculate_varshaphal,
)
from vedic_calc.core.constants import Ayanamsa, Planet, Sign
from vedic_calc.kp.significators import get_kp_significators, get_kp_house_significators


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mumbai_chart():
    """Birth chart: March 15, 1990, 10:30 AM IST, Mumbai."""
    return calculate_chart(
        year=1990, month=3, day=15,
        hour=10, minute=30,
        latitude=19.076, longitude=72.878,
        timezone_offset=5.5,
        ayanamsa=Ayanamsa.LAHIRI,
    )


@pytest.fixture
def delhi_chart():
    """Birth chart: July 20, 1985, 2:00 PM IST, Delhi."""
    return calculate_chart(
        year=1985, month=7, day=20,
        hour=14, minute=0,
        latitude=28.6139, longitude=77.209,
        timezone_offset=5.5,
        ayanamsa=Ayanamsa.LAHIRI,
    )


@pytest.fixture
def kp_chart():
    """KP chart: March 15, 1990, 10:30 AM IST, Mumbai."""
    return calculate_kp_chart(
        year=1990, month=3, day=15,
        hour=10, minute=30, second=0,
        latitude=19.076, longitude=72.878,
        timezone_offset=5.5,
    )


# ===========================================================================
# 10. Sookshma Dasha (levels=4)
# ===========================================================================

class TestSookshmaDasha:
    def test_returns_sookshmadasha_level(self, mumbai_chart):
        """levels=4 should produce periods at the 'sookshmadasha' level."""
        periods = calculate_dasha(mumbai_chart, levels=4)
        sookshma = [p for p in periods if p.level == "sookshmadasha"]
        assert len(sookshma) > 0, "No sookshmadasha periods found"

    def test_count_exceeds_levels3(self, mumbai_chart):
        """levels=4 should produce more periods than levels=3."""
        periods_3 = calculate_dasha(mumbai_chart, levels=3)
        periods_4 = calculate_dasha(mumbai_chart, levels=4)
        assert len(periods_4) > len(periods_3)

    def test_expected_sookshmadasha_count(self, mumbai_chart):
        """There should be 9^4 = 6561 sookshmadasha periods across the full 120 years."""
        periods = calculate_dasha(mumbai_chart, levels=4)
        sookshma = [p for p in periods if p.level == "sookshmadasha"]
        assert len(sookshma) == 9 ** 4

    def test_sookshma_durations_sum_to_parent(self, mumbai_chart):
        """Sookshmadasha durations within one pratyantardasha should sum to the parent duration."""
        periods = calculate_dasha(mumbai_chart, levels=4)
        pratyantars = [p for p in periods if p.level == "pratyantardasha"]
        sookshmas = [p for p in periods if p.level == "sookshmadasha"]

        # Check first pratyantardasha
        first_prat = pratyantars[0]
        children = [
            s for s in sookshmas
            if s.start >= first_prat.start and s.end <= first_prat.end + __import__("datetime").timedelta(seconds=1)
        ]
        child_sum = sum(c.duration_years for c in children)
        assert abs(child_sum - first_prat.duration_years) < 0.001, (
            f"Sookshma sum {child_sum:.6f} != pratyantardasha {first_prat.duration_years:.6f}"
        )

    def test_sookshma_periods_have_valid_lords(self, mumbai_chart):
        """All sookshmadasha lords should be valid Planet enum members."""
        periods = calculate_dasha(mumbai_chart, levels=4)
        sookshma = [p for p in periods if p.level == "sookshmadasha"]
        for s in sookshma[:100]:  # check first 100 to keep test fast
            assert isinstance(s.lord, Planet)

    def test_sookshma_periods_chronological(self, mumbai_chart):
        """Sookshmadasha periods should be chronologically ordered within same parent."""
        periods = calculate_dasha(mumbai_chart, levels=4)
        sookshma = [p for p in periods if p.level == "sookshmadasha"]
        for i in range(min(100, len(sookshma) - 1)):
            assert sookshma[i].start <= sookshma[i + 1].start


# ===========================================================================
# 10b. Prana Dasha (levels=5)
# ===========================================================================

class TestPranaDasha:
    def test_returns_pranadasha_level(self, mumbai_chart):
        """levels=5 should produce periods at the 'pranadasha' level."""
        # Only compute levels=5 for a single mahadasha to keep it fast
        periods = calculate_dasha(mumbai_chart, levels=5)
        prana = [p for p in periods if p.level == "pranadasha"]
        assert len(prana) > 0, "No pranadasha periods found"

    def test_count_exceeds_levels4(self, mumbai_chart):
        """levels=5 should produce more periods than levels=4."""
        periods_4 = calculate_dasha(mumbai_chart, levels=4)
        periods_5 = calculate_dasha(mumbai_chart, levels=5)
        assert len(periods_5) > len(periods_4)

    def test_pranadasha_has_valid_lord(self, mumbai_chart):
        """Prana dasha lords should be valid Planet members."""
        periods = calculate_dasha(mumbai_chart, levels=5)
        prana = [p for p in periods if p.level == "pranadasha"]
        for p in prana[:50]:
            assert isinstance(p.lord, Planet)

    def test_pranadasha_durations_positive(self, mumbai_chart):
        """All prana dasha durations should be positive."""
        periods = calculate_dasha(mumbai_chart, levels=5)
        prana = [p for p in periods if p.level == "pranadasha"]
        for p in prana[:50]:
            assert p.duration_years > 0


# ===========================================================================
# 11. KP Significators
# ===========================================================================

class TestKPSignificators:
    def test_per_planet_returns_9_entries(self, mumbai_chart):
        """Should return one KPSignificatorDetail per planet (9 total)."""
        result = get_kp_significators(mumbai_chart)
        assert len(result) == 9

    def test_per_planet_has_4_levels(self, mumbai_chart):
        """Each planet should have all 4 signification levels."""
        result = get_kp_significators(mumbai_chart)
        for detail in result:
            assert hasattr(detail, "level1_houses")
            assert hasattr(detail, "level2_houses")
            assert hasattr(detail, "level3_houses")
            assert hasattr(detail, "level4_houses")
            assert hasattr(detail, "all_signified_houses")

    def test_level1_houses_non_empty(self, mumbai_chart):
        """Level 1 (houses occupied) should have exactly 1 house per planet."""
        result = get_kp_significators(mumbai_chart)
        for detail in result:
            assert len(detail.level1_houses) == 1
            assert 1 <= detail.level1_houses[0] <= 12

    def test_all_signified_is_union(self, mumbai_chart):
        """all_signified_houses should be the sorted union of all 4 levels."""
        result = get_kp_significators(mumbai_chart)
        for detail in result:
            expected = sorted(set(
                detail.level1_houses + detail.level2_houses
                + detail.level3_houses + detail.level4_houses
            ))
            assert detail.all_signified_houses == expected

    def test_houses_in_valid_range(self, mumbai_chart):
        """All house numbers should be 1-12."""
        result = get_kp_significators(mumbai_chart)
        for detail in result:
            for h in detail.all_signified_houses:
                assert 1 <= h <= 12

    def test_per_house_covers_all_12(self, mumbai_chart):
        """Per-house significators should cover all 12 houses."""
        result = get_kp_house_significators(mumbai_chart)
        assert len(result) == 12
        house_nums = {r.house_number for r in result}
        assert house_nums == set(range(1, 13))

    def test_per_house_significators_are_valid_planets(self, mumbai_chart):
        """Each house's significator planets should be valid Planet members."""
        result = get_kp_house_significators(mumbai_chart)
        for house_sig in result:
            for planet in house_sig.significators:
                assert isinstance(planet, Planet)

    def test_per_house_at_least_one_significator(self, mumbai_chart):
        """Each house should have at least one significator planet."""
        result = get_kp_house_significators(mumbai_chart)
        for house_sig in result:
            assert len(house_sig.significators) >= 1, (
                f"House {house_sig.house_number} has no significators"
            )


# ===========================================================================
# 12. Sudarshana Chakra
# ===========================================================================

class TestSudarshanaChakra:
    def test_has_3_rings(self, mumbai_chart):
        """Sudarshana Chakra should have lagna, moon, and sun rings."""
        chakra = calculate_sudarshana_chakra(mumbai_chart)
        assert hasattr(chakra, "lagna_ring")
        assert hasattr(chakra, "moon_ring")
        assert hasattr(chakra, "sun_ring")

    def test_each_ring_has_12_houses(self, mumbai_chart):
        """Each ring should have exactly 12 houses."""
        chakra = calculate_sudarshana_chakra(mumbai_chart)
        assert len(chakra.lagna_ring) == 12
        assert len(chakra.moon_ring) == 12
        assert len(chakra.sun_ring) == 12

    def test_house_numbers_1_to_12(self, mumbai_chart):
        """Each ring should have houses numbered 1-12."""
        chakra = calculate_sudarshana_chakra(mumbai_chart)
        for ring in [chakra.lagna_ring, chakra.moon_ring, chakra.sun_ring]:
            nums = {h.house_number for h in ring}
            assert nums == set(range(1, 13))

    def test_lagna_ring_starts_from_ascendant(self, mumbai_chart):
        """House 1 of lagna ring should have the ascendant sign."""
        chakra = calculate_sudarshana_chakra(mumbai_chart)
        assert chakra.lagna_ring[0].sign == mumbai_chart.ascendant.sign

    def test_moon_ring_starts_from_moon_sign(self, mumbai_chart):
        """House 1 of moon ring should have the Moon's sign."""
        chakra = calculate_sudarshana_chakra(mumbai_chart)
        moon_sign = mumbai_chart.planets[Planet.MOON].sign
        assert chakra.moon_ring[0].sign == moon_sign

    def test_sun_ring_starts_from_sun_sign(self, mumbai_chart):
        """House 1 of sun ring should have the Sun's sign."""
        chakra = calculate_sudarshana_chakra(mumbai_chart)
        sun_sign = mumbai_chart.planets[Planet.SUN].sign
        assert chakra.sun_ring[0].sign == sun_sign

    def test_each_ring_has_12_unique_signs(self, mumbai_chart):
        """Each ring should cover all 12 signs (one per house)."""
        chakra = calculate_sudarshana_chakra(mumbai_chart)
        for ring in [chakra.lagna_ring, chakra.moon_ring, chakra.sun_ring]:
            signs = {h.sign for h in ring}
            assert len(signs) == 12

    def test_planets_distributed_across_ring(self, mumbai_chart):
        """All 9 planets should appear exactly once across the 12 houses of each ring."""
        chakra = calculate_sudarshana_chakra(mumbai_chart)
        for ring in [chakra.lagna_ring, chakra.moon_ring, chakra.sun_ring]:
            all_planets = []
            for house in ring:
                all_planets.extend(house.planets)
            assert len(all_planets) == 9, f"Expected 9 planets, got {len(all_planets)}"
            assert set(all_planets) == set(Planet)

    def test_houses_contain_valid_planets(self, mumbai_chart):
        """All planets in houses should be valid Planet enum members."""
        chakra = calculate_sudarshana_chakra(mumbai_chart)
        for ring in [chakra.lagna_ring, chakra.moon_ring, chakra.sun_ring]:
            for house in ring:
                for planet in house.planets:
                    assert isinstance(planet, Planet)


# ===========================================================================
# 13. Papasamyam
# ===========================================================================

class TestPapasamyam:
    def test_returns_valid_result(self, mumbai_chart, delhi_chart):
        """Should return a PapasamyamResult with person1, person2, and balance."""
        result = calculate_papasamyam(mumbai_chart, delhi_chart)
        assert hasattr(result, "person1")
        assert hasattr(result, "person2")
        assert hasattr(result, "is_balanced")
        assert hasattr(result, "difference")
        assert hasattr(result, "description")

    def test_malefic_points_non_negative(self, mumbai_chart, delhi_chart):
        """All malefic scores should be non-negative."""
        result = calculate_papasamyam(mumbai_chart, delhi_chart)
        for person in [result.person1, result.person2]:
            assert person.lagna_score >= 0
            assert person.moon_score >= 0
            assert person.venus_score >= 0
            assert person.total >= 0

    def test_total_equals_sum_of_parts(self, mumbai_chart, delhi_chart):
        """Total should equal lagna + moon + venus scores."""
        result = calculate_papasamyam(mumbai_chart, delhi_chart)
        for person in [result.person1, result.person2]:
            expected = person.lagna_score + person.moon_score + person.venus_score
            assert abs(person.total - expected) < 0.01

    def test_balanced_flag_is_boolean(self, mumbai_chart, delhi_chart):
        """is_balanced should be a boolean."""
        result = calculate_papasamyam(mumbai_chart, delhi_chart)
        assert isinstance(result.is_balanced, bool)

    def test_difference_matches_totals(self, mumbai_chart, delhi_chart):
        """difference should equal abs(person1.total - person2.total)."""
        result = calculate_papasamyam(mumbai_chart, delhi_chart)
        expected_diff = abs(result.person1.total - result.person2.total)
        assert abs(result.difference - expected_diff) < 0.01

    def test_description_not_empty(self, mumbai_chart, delhi_chart):
        """Description should be a non-empty string."""
        result = calculate_papasamyam(mumbai_chart, delhi_chart)
        assert len(result.description) > 0

    def test_balanced_when_both_low(self):
        """Two identical charts should be balanced (same malefic load)."""
        chart = calculate_chart(
            year=1990, month=3, day=15,
            hour=10, minute=30,
            latitude=19.076, longitude=72.878,
            timezone_offset=5.5,
        )
        result = calculate_papasamyam(chart, chart)
        assert result.is_balanced is True
        assert result.difference == 0.0

    def test_order_does_not_affect_balance(self, mumbai_chart, delhi_chart):
        """Swapping chart order should give the same balance result."""
        result1 = calculate_papasamyam(mumbai_chart, delhi_chart)
        result2 = calculate_papasamyam(delhi_chart, mumbai_chart)
        assert result1.is_balanced == result2.is_balanced
        assert abs(result1.difference - result2.difference) < 0.01


# ===========================================================================
# 14a. Panchavargeeya Bala
# ===========================================================================

class TestPanchavargeeaBala:
    def test_one_result_per_planet(self, mumbai_chart):
        """Should return one PanchavargeeaBala per planet (9 total)."""
        # Need an annual chart for panchavargeeya bala
        varsha = calculate_varshaphal(mumbai_chart, 2025)
        result = calculate_panchavargeeya_bala(varsha.annual_chart)
        assert len(result) == 9
        planets = {r.planet for r in result}
        assert planets == set(Planet)

    def test_total_points_in_valid_range(self, mumbai_chart):
        """total_points should be between 0 and 20 (5 divisions x max 4 pts each)."""
        varsha = calculate_varshaphal(mumbai_chart, 2025)
        result = calculate_panchavargeeya_bala(varsha.annual_chart)
        for bala in result:
            assert 0 <= bala.total_points <= 20, (
                f"{bala.planet.name}: total_points={bala.total_points} out of range"
            )

    def test_all_5_dignity_fields_present(self, mumbai_chart):
        """Each result should have d1, d2, d3, d9, d12 dignity fields."""
        varsha = calculate_varshaphal(mumbai_chart, 2025)
        result = calculate_panchavargeeya_bala(varsha.annual_chart)
        valid_dignities = {"exalted", "moolatrikona", "own", "friend", "neutral", "enemy", "debilitated"}
        for bala in result:
            assert bala.d1_dignity in valid_dignities, f"{bala.planet.name} d1: {bala.d1_dignity}"
            assert bala.d2_dignity in valid_dignities, f"{bala.planet.name} d2: {bala.d2_dignity}"
            assert bala.d3_dignity in valid_dignities, f"{bala.planet.name} d3: {bala.d3_dignity}"
            assert bala.d9_dignity in valid_dignities, f"{bala.planet.name} d9: {bala.d9_dignity}"
            assert bala.d12_dignity in valid_dignities, f"{bala.planet.name} d12: {bala.d12_dignity}"

    def test_total_matches_sum_of_dignities(self, mumbai_chart):
        """total_points should match the sum of individual dignity point values."""
        varsha = calculate_varshaphal(mumbai_chart, 2025)
        result = calculate_panchavargeeya_bala(varsha.annual_chart)
        dignity_points = {
            "exalted": 4.0, "moolatrikona": 3.5, "own": 3.0,
            "friend": 2.0, "neutral": 1.5, "enemy": 1.0, "debilitated": 0.5,
        }
        for bala in result:
            expected = (
                dignity_points[bala.d1_dignity]
                + dignity_points[bala.d2_dignity]
                + dignity_points[bala.d3_dignity]
                + dignity_points[bala.d9_dignity]
                + dignity_points[bala.d12_dignity]
            )
            assert abs(bala.total_points - expected) < 0.01, (
                f"{bala.planet.name}: total={bala.total_points}, expected={expected}"
            )


# ===========================================================================
# 14b. Mudda Dasha with levels=2 (antardashas)
# ===========================================================================

class TestMuddaDashaAntardashas:
    def test_varshaphal_has_mudda_dasha(self, mumbai_chart):
        """Varshaphal result should contain mudda_dasha periods."""
        varsha = calculate_varshaphal(mumbai_chart, 2025)
        assert len(varsha.mudda_dasha) > 0

    def test_mudda_dasha_mahadasha_count(self, mumbai_chart):
        """Should have exactly 9 mudda_dasha mahadasha periods."""
        varsha = calculate_varshaphal(mumbai_chart, 2025)
        mahas = [p for p in varsha.mudda_dasha if p.level == "mudda_dasha"]
        assert len(mahas) == 9

    def test_mudda_dasha_total_covers_one_year(self, mumbai_chart):
        """Mudda dasha mahadasha durations should sum to ~1 year."""
        varsha = calculate_varshaphal(mumbai_chart, 2025)
        mahas = [p for p in varsha.mudda_dasha if p.level == "mudda_dasha"]
        total_years = sum(p.duration_years for p in mahas)
        assert abs(total_years - 1.0) < 0.01, f"Total Mudda years={total_years}"

    def test_mudda_antardasha_with_levels2(self, mumbai_chart):
        """calculate_varshaphal with mudda levels=2 should produce antardasha sub-periods."""
        # Varshaphal internally calls _calculate_mudda_dasha with levels=1 by default.
        # We need to call _calculate_mudda_dasha directly with levels=2.
        from vedic_calc.varshaphal.calculator import _calculate_mudda_dasha

        varsha = calculate_varshaphal(mumbai_chart, 2025)
        mudda_with_antar = _calculate_mudda_dasha(
            varsha.annual_chart, varsha.solar_return_datetime, levels=2,
        )

        antars = [p for p in mudda_with_antar if p.level == "mudda_antardasha"]
        assert len(antars) > 0, "No mudda_antardasha periods found"
        # Should be 9 * 9 = 81 antardashas
        assert len(antars) == 81

    def test_mudda_antardasha_durations_sum_to_parent(self, mumbai_chart):
        """Mudda antardasha durations within one mahadasha should sum to the parent."""
        from vedic_calc.varshaphal.calculator import _calculate_mudda_dasha

        varsha = calculate_varshaphal(mumbai_chart, 2025)
        mudda = _calculate_mudda_dasha(
            varsha.annual_chart, varsha.solar_return_datetime, levels=2,
        )

        mahas = [p for p in mudda if p.level == "mudda_dasha"]
        antars = [p for p in mudda if p.level == "mudda_antardasha"]

        # Check first mahadasha
        first_maha = mahas[0]
        from datetime import timedelta
        children = [
            a for a in antars
            if a.start >= first_maha.start and a.end <= first_maha.end + timedelta(seconds=1)
        ]
        child_sum = sum(c.duration_years for c in children)
        assert abs(child_sum - first_maha.duration_years) < 0.001, (
            f"Antardasha sum {child_sum:.6f} != mahadasha {first_maha.duration_years:.6f}"
        )

    def test_mudda_antardasha_total_covers_one_year(self, mumbai_chart):
        """All mudda antardasha durations should sum to ~1 year."""
        from vedic_calc.varshaphal.calculator import _calculate_mudda_dasha

        varsha = calculate_varshaphal(mumbai_chart, 2025)
        mudda = _calculate_mudda_dasha(
            varsha.annual_chart, varsha.solar_return_datetime, levels=2,
        )

        antars = [p for p in mudda if p.level == "mudda_antardasha"]
        total_years = sum(p.duration_years for p in antars)
        assert abs(total_years - 1.0) < 0.01, f"Total Mudda antardasha years={total_years}"

    def test_mudda_periods_have_valid_lords(self, mumbai_chart):
        """All Mudda dasha lords should be valid Planet members."""
        varsha = calculate_varshaphal(mumbai_chart, 2025)
        for period in varsha.mudda_dasha:
            assert isinstance(period.lord, Planet)
