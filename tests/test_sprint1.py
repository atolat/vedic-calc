"""Tests for Sprint 1 features: helpers, avakhada, disha shool, anandadi yoga,
planet relationships, sade sati, chandrashtama, functional nature, and chalit chart.

Uses a shared Mumbai birth chart fixture consistent with the rest of the test suite.
"""

from datetime import datetime, timedelta

import pytest

from vedic_calc import calculate_chart
from vedic_calc.core.constants import Ayanamsa, Nakshatra, Planet, Sign, PLANET_FRIENDSHIP
from vedic_calc.core.helpers import sign_distance, planet_house
from vedic_calc.compatibility.avakhada import calculate_avakhada
from vedic_calc.muhurta.calculator import get_disha_shool
from vedic_calc.panchanga.calculator import get_anandadi_yoga
from vedic_calc.chart.relationships import calculate_planet_relationships
from vedic_calc.chart.sade_sati import calculate_sade_sati, calculate_sade_sati_periods
from vedic_calc.chart.chandrashtama import calculate_chandrashtama
from vedic_calc.chart.functional import calculate_functional_nature
from vedic_calc.chart.chalit import calculate_chalit_chart


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def mumbai_chart():
    """Birth chart: March 15, 1990, 10:30 AM IST, Mumbai."""
    return calculate_chart(
        year=1990, month=3, day=15,
        hour=10, minute=30,
        latitude=19.0760, longitude=72.8777,
        timezone_offset=5.5,
        ayanamsa=Ayanamsa.LAHIRI,
    )


# ===========================================================================
# 1. Core Helpers
# ===========================================================================

class TestSignDistance:
    def test_same_sign_returns_1(self):
        assert sign_distance(Sign.ARIES, Sign.ARIES) == 1

    def test_adjacent_sign_returns_2(self):
        assert sign_distance(Sign.ARIES, Sign.TAURUS) == 2

    def test_aries_to_pisces_returns_12(self):
        assert sign_distance(Sign.ARIES, Sign.PISCES) == 12

    def test_pisces_to_aries_returns_2(self):
        assert sign_distance(Sign.PISCES, Sign.ARIES) == 2

    def test_cancer_to_aquarius_returns_8(self):
        """8th from Cancer is Aquarius (used in chandrashtama)."""
        assert sign_distance(Sign.CANCER, Sign.AQUARIUS) == 8

    def test_all_distances_in_range(self):
        """All sign distances should be 1-12."""
        for s1 in Sign:
            for s2 in Sign:
                d = sign_distance(s1, s2)
                assert 1 <= d <= 12, f"{s1}->{s2}: {d}"


class TestPlanetHouse:
    def test_returns_valid_house(self, mumbai_chart):
        for planet in Planet:
            h = planet_house(mumbai_chart, planet)
            assert 1 <= h <= 12, f"{planet.name}: house {h}"

    def test_sun_house_matches_sign(self, mumbai_chart):
        """Sun's house should match the house whose sign equals Sun's sign."""
        sun_sign = mumbai_chart.planets[Planet.SUN].sign
        sun_h = planet_house(mumbai_chart, Planet.SUN)
        assert mumbai_chart.houses[sun_h - 1].sign == sun_sign


# ===========================================================================
# 2. Avakhada Table
# ===========================================================================

class TestAvakhada:
    def test_ashwini_pada1_aries(self):
        info = calculate_avakhada(Nakshatra.ASHWINI, 1, Sign.ARIES)
        assert info.yoni == "Horse"
        assert info.gana == "Deva"
        assert info.name_letter == "Chu"
        assert info.varna == "Vaishya"

    def test_rohini_pada2_taurus(self):
        info = calculate_avakhada(Nakshatra.ROHINI, 2, Sign.TAURUS)
        assert info.name_letter == "Va"
        assert info.yoni == "Serpent"

    def test_all_fields_populated(self):
        info = calculate_avakhada(Nakshatra.ASHWINI, 1, Sign.ARIES)
        assert info.varna != ""
        assert info.vashya != ""
        assert info.yoni != ""
        assert info.gana != ""
        assert info.nadi != ""
        assert info.name_letter != ""
        assert info.tatva != ""
        assert info.yunja != ""
        assert info.paya != ""
        assert info.nakshatra_lord is not None
        assert info.sign_lord is not None

    def test_invalid_pada_raises(self):
        with pytest.raises(ValueError, match="pada must be 1-4"):
            calculate_avakhada(Nakshatra.ASHWINI, 5, Sign.ARIES)

    def test_yunja_by_pada(self):
        assert calculate_avakhada(Nakshatra.ASHWINI, 1, Sign.ARIES).yunja == "Poorva"
        assert calculate_avakhada(Nakshatra.ASHWINI, 2, Sign.ARIES).yunja == "Madhya"
        assert calculate_avakhada(Nakshatra.ASHWINI, 3, Sign.ARIES).yunja == "Madhya"
        assert calculate_avakhada(Nakshatra.ASHWINI, 4, Sign.ARIES).yunja == "Antya"


# ===========================================================================
# 3. Disha Shool
# ===========================================================================

class TestDishaShool:
    def test_monday_east(self):
        # 2026-03-09 is Monday
        info = get_disha_shool(2026, 3, 9)
        assert info.direction == "East"
        assert info.weekday == "Monday"

    def test_tuesday_north(self):
        # 2026-03-10 is Tuesday
        info = get_disha_shool(2026, 3, 10)
        assert info.direction == "North"

    def test_friday_west(self):
        # 2026-03-13 is Friday
        info = get_disha_shool(2026, 3, 13)
        assert info.direction == "West"

    def test_sunday_south(self):
        # 2026-03-08 is Sunday
        info = get_disha_shool(2026, 3, 8)
        assert info.direction == "South"

    def test_description_contains_direction(self):
        info = get_disha_shool(2026, 3, 8)
        assert info.direction in info.description


# ===========================================================================
# 4. Anandadi Yoga
# ===========================================================================

class TestAnandadiYoga:
    VALID_QUALITIES = {"auspicious", "inauspicious"}
    ALL_YOGA_NAMES = {"Ananda", "Kaldanda", "Dhoomra", "Chora", "Roga", "Kala", "Siddha", "Subha"}

    def test_quality_valid(self):
        info = get_anandadi_yoga(1, 0)  # Pratipada on Monday
        assert info.quality in self.VALID_QUALITIES

    def test_all_8_yogas_reachable(self):
        """By varying tithi and weekday, all 8 yoga names should appear."""
        seen = set()
        for tithi in range(1, 31):
            for weekday in range(7):
                info = get_anandadi_yoga(tithi, weekday)
                seen.add(info.yoga_name)
                if seen == self.ALL_YOGA_NAMES:
                    break
            if seen == self.ALL_YOGA_NAMES:
                break
        assert seen == self.ALL_YOGA_NAMES

    def test_known_combination(self):
        """Pratipada (tithi=1) on Monday (weekday=0) should give Kaldanda."""
        info = get_anandadi_yoga(1, 0)
        assert info.yoga_name == "Kaldanda"

    def test_description_not_empty(self):
        info = get_anandadi_yoga(5, 3)
        assert len(info.description) > 0


# ===========================================================================
# 5. Planet Relationships
# ===========================================================================

class TestPlanetRelationships:
    CLASSICAL_PLANETS = [
        Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
        Planet.JUPITER, Planet.VENUS, Planet.SATURN,
    ]
    VALID_NATURAL = {"friend", "neutral", "enemy"}
    VALID_TEMPORAL = {"friend", "enemy"}
    VALID_COMPOUND = {"great_friend", "friend", "neutral", "enemy", "great_enemy"}

    def test_has_all_7_planets(self, mumbai_chart):
        result = calculate_planet_relationships(mumbai_chart)
        for p in self.CLASSICAL_PLANETS:
            assert p in result.relationships

    def test_each_planet_has_6_relationships(self, mumbai_chart):
        result = calculate_planet_relationships(mumbai_chart)
        for p in self.CLASSICAL_PLANETS:
            assert len(result.relationships[p]) == 6

    def test_natural_values_match_constant(self, mumbai_chart):
        result = calculate_planet_relationships(mumbai_chart)
        natural_labels = {0: "enemy", 1: "neutral", 2: "friend"}
        for p in self.CLASSICAL_PLANETS:
            for rel in result.relationships[p]:
                expected = natural_labels[PLANET_FRIENDSHIP[p][rel.other_planet]]
                assert rel.natural == expected, (
                    f"{p.name}->{rel.other_planet.name}: got {rel.natural}, expected {expected}"
                )

    def test_temporal_values_valid(self, mumbai_chart):
        result = calculate_planet_relationships(mumbai_chart)
        for p in self.CLASSICAL_PLANETS:
            for rel in result.relationships[p]:
                assert rel.temporal in self.VALID_TEMPORAL

    def test_compound_values_valid(self, mumbai_chart):
        result = calculate_planet_relationships(mumbai_chart)
        for p in self.CLASSICAL_PLANETS:
            for rel in result.relationships[p]:
                assert rel.compound in self.VALID_COMPOUND


# ===========================================================================
# 6. Sade Sati
# ===========================================================================

class TestSadeSati:
    def test_calculate_returns_result(self, mumbai_chart):
        result = calculate_sade_sati(mumbai_chart)
        assert hasattr(result, "is_active")
        assert hasattr(result, "current_phase")
        assert hasattr(result, "moon_sign")
        assert result.moon_sign == mumbai_chart.planets[Planet.MOON].sign

    def test_calculate_with_date(self, mumbai_chart):
        result = calculate_sade_sati(mumbai_chart, target_date=datetime(2026, 1, 1))
        assert isinstance(result.is_active, bool)
        if result.is_active:
            assert result.current_phase in {"rising", "peak", "setting"}
        else:
            assert result.current_phase is None

    def test_periods_over_30_years(self, mumbai_chart):
        start = datetime(1990, 1, 1)
        end = datetime(2020, 1, 1)
        result = calculate_sade_sati_periods(mumbai_chart, start, end)
        # Saturn takes ~29.5 years to orbit, so in 30 years we should see
        # at least some phases
        assert len(result.phases) > 0

    def test_phase_names_valid(self, mumbai_chart):
        start = datetime(1990, 1, 1)
        end = datetime(2020, 1, 1)
        result = calculate_sade_sati_periods(mumbai_chart, start, end)
        for phase in result.phases:
            assert phase.phase in {"rising", "peak", "setting"}

    def test_phases_chronological(self, mumbai_chart):
        start = datetime(1990, 1, 1)
        end = datetime(2020, 1, 1)
        result = calculate_sade_sati_periods(mumbai_chart, start, end)
        for i in range(len(result.phases) - 1):
            assert result.phases[i].start <= result.phases[i + 1].start


# ===========================================================================
# 7. Chandrashtama
# ===========================================================================

class TestChandrashtama:
    def test_cancer_moon_30_days(self):
        start = datetime(2026, 3, 1)
        end = datetime(2026, 3, 31)
        result = calculate_chandrashtama(
            natal_moon_sign=Sign.CANCER,
            start_date=start,
            end_date=end,
            timezone_offset=5.5,
        )
        # 8th from Cancer is Aquarius
        assert result.chandrashtama_sign == Sign.AQUARIUS
        assert result.natal_moon_sign == Sign.CANCER
        # Moon passes through each sign roughly once per ~27 days,
        # so should find at least 1 window in 30 days
        assert len(result.windows) >= 1

    def test_window_duration_reasonable(self):
        start = datetime(2026, 3, 1)
        end = datetime(2026, 3, 31)
        result = calculate_chandrashtama(
            natal_moon_sign=Sign.CANCER,
            start_date=start,
            end_date=end,
            timezone_offset=5.5,
        )
        for w in result.windows:
            duration = w.end - w.start
            # Moon spends ~2-3 days in a sign
            assert timedelta(hours=12) < duration < timedelta(days=4), (
                f"Window duration {duration} out of expected range"
            )
            assert w.transit_sign == Sign.AQUARIUS

    def test_eighth_sign_correctness(self):
        """Verify the 8th sign mapping for several natal signs."""
        cases = [
            (Sign.ARIES, Sign.SCORPIO),
            (Sign.TAURUS, Sign.SAGITTARIUS),
            (Sign.CANCER, Sign.AQUARIUS),
            (Sign.LEO, Sign.PISCES),
            (Sign.SCORPIO, Sign.GEMINI),
        ]
        start = datetime(2026, 3, 1)
        end = datetime(2026, 3, 10)
        for natal, expected_8th in cases:
            result = calculate_chandrashtama(
                natal_moon_sign=natal,
                start_date=start,
                end_date=end,
                timezone_offset=5.5,
            )
            assert result.chandrashtama_sign == expected_8th, (
                f"8th from {natal.name}: expected {expected_8th.name}, got {result.chandrashtama_sign.name}"
            )


# ===========================================================================
# 8. Functional Nature
# ===========================================================================

class TestFunctionalNature:
    VALID_NATURES = {"yogakaraka", "benefic", "malefic", "neutral"}

    def test_returns_9_entries(self, mumbai_chart):
        result = calculate_functional_nature(mumbai_chart)
        assert len(result) == 9

    def test_all_natures_valid(self, mumbai_chart):
        result = calculate_functional_nature(mumbai_chart)
        for fn in result:
            assert fn.nature in self.VALID_NATURES, f"{fn.planet.name}: {fn.nature}"

    def test_has_description(self, mumbai_chart):
        result = calculate_functional_nature(mumbai_chart)
        for fn in result:
            assert len(fn.description) > 0

    def test_rahu_ketu_neutral(self, mumbai_chart):
        """Rahu and Ketu should be neutral (no house lordship)."""
        result = calculate_functional_nature(mumbai_chart)
        for fn in result:
            if fn.planet in (Planet.RAHU, Planet.KETU):
                assert fn.nature == "neutral"
                assert fn.ruled_houses == []

    def test_at_least_one_benefic_and_malefic(self, mumbai_chart):
        result = calculate_functional_nature(mumbai_chart)
        natures = {fn.nature for fn in result}
        # For any lagna, there should be at least one benefic and one malefic
        assert "benefic" in natures or "yogakaraka" in natures
        assert "malefic" in natures


# ===========================================================================
# 9. Chalit Chart
# ===========================================================================

class TestChalitChart:
    def test_has_12_houses(self, mumbai_chart):
        chalit = calculate_chalit_chart(mumbai_chart)
        assert len(chalit.houses) == 12

    def test_bhav_madhya_house1_equals_ascendant(self, mumbai_chart):
        chalit = calculate_chalit_chart(mumbai_chart)
        asc_lon = mumbai_chart.ascendant.longitude
        assert abs(chalit.houses[0].bhav_madhya - (asc_lon % 360)) < 0.01

    def test_all_planets_placed(self, mumbai_chart):
        chalit = calculate_chalit_chart(mumbai_chart)
        assert len(chalit.planet_houses) == 9
        for planet in Planet:
            assert planet in chalit.planet_houses

    def test_house_numbers_1_to_12(self, mumbai_chart):
        chalit = calculate_chalit_chart(mumbai_chart)
        house_nums = {h.house_number for h in chalit.houses}
        assert house_nums == set(range(1, 13))

    def test_planet_houses_in_range(self, mumbai_chart):
        chalit = calculate_chalit_chart(mumbai_chart)
        for planet, house_num in chalit.planet_houses.items():
            assert 1 <= house_num <= 12, f"{planet.name}: house {house_num}"

    def test_bhav_madhya_30_degree_spacing(self, mumbai_chart):
        """Consecutive bhav madhyas should be ~30 degrees apart."""
        chalit = calculate_chalit_chart(mumbai_chart)
        for i in range(11):
            m1 = chalit.houses[i].bhav_madhya
            m2 = chalit.houses[i + 1].bhav_madhya
            diff = (m2 - m1) % 360
            assert abs(diff - 30.0) < 0.1, f"House {i+1}->{i+2}: diff={diff}"
