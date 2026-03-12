"""Tests for Jaimini astrology calculations (Karakas, Arudha Padas)."""

import pytest

from vedic_calc import calculate_chart
from vedic_calc.core.constants import Planet, Sign
from vedic_calc.jaimini.karakas import calculate_chara_karakas
from vedic_calc.jaimini.arudha import calculate_arudha_padas


@pytest.fixture
def mumbai_chart():
    return calculate_chart(
        year=1990, month=3, day=15, hour=10, minute=30,
        latitude=19.0760, longitude=72.8777, timezone_offset=5.5,
    )


class TestCharaKarakas:
    def test_returns_8_karakas(self, mumbai_chart):
        karakas = calculate_chara_karakas(mumbai_chart)
        assert len(karakas) == 8

    def test_first_is_atmakaraka(self, mumbai_chart):
        karakas = calculate_chara_karakas(mumbai_chart)
        assert karakas[0].karaka_name == "Atmakaraka"

    def test_last_is_pitrkaraka(self, mumbai_chart):
        karakas = calculate_chara_karakas(mumbai_chart)
        assert karakas[7].karaka_name == "Pitrkaraka"

    def test_no_duplicate_planets(self, mumbai_chart):
        karakas = calculate_chara_karakas(mumbai_chart)
        planets = [k.planet for k in karakas]
        assert len(set(planets)) == 8

    def test_ketu_excluded(self, mumbai_chart):
        karakas = calculate_chara_karakas(mumbai_chart)
        planets = {k.planet for k in karakas}
        assert Planet.KETU not in planets

    def test_degrees_descending(self, mumbai_chart):
        """Degrees should be in descending order (AK has highest)."""
        karakas = calculate_chara_karakas(mumbai_chart)
        degrees = [k.degree_in_sign for k in karakas]
        for i in range(len(degrees) - 1):
            assert degrees[i] >= degrees[i + 1]


class TestArudhaPadas:
    def test_returns_12_padas(self, mumbai_chart):
        padas = calculate_arudha_padas(mumbai_chart)
        assert len(padas) == 12

    def test_house_numbers_sequential(self, mumbai_chart):
        padas = calculate_arudha_padas(mumbai_chart)
        for i, pada in enumerate(padas):
            assert pada.house_number == i + 1

    def test_valid_signs(self, mumbai_chart):
        padas = calculate_arudha_padas(mumbai_chart)
        for pada in padas:
            assert 1 <= pada.sign.value <= 12

    def test_first_is_arudha_lagna(self, mumbai_chart):
        padas = calculate_arudha_padas(mumbai_chart)
        assert "AL" in padas[0].pada_name or "Arudha Lagna" in padas[0].pada_name
