"""Tests for the numerology module (Chaldean + Vedic system)."""

from __future__ import annotations

from unittest.mock import patch
from datetime import date

import pytest

from vedic_calc.numerology.calculator import (
    _reduce_to_single,
    _chaldean_value,
    calculate_numerology,
)
from vedic_calc.core.types import NumerologyResult


class TestDigitReduction:
    """Test _reduce_to_single helper."""

    def test_single_digit_unchanged(self):
        assert _reduce_to_single(5) == 5
        assert _reduce_to_single(1) == 1
        assert _reduce_to_single(9) == 9

    def test_28_reduces_to_1(self):
        # 2+8 = 10 → 1+0 = 1
        assert _reduce_to_single(28) == 1

    def test_19_reduces_to_1(self):
        # 1+9 = 10 → 1+0 = 1
        assert _reduce_to_single(19) == 1

    def test_29_reduces_to_2(self):
        # 2+9 = 11 → 1+1 = 2 (no master number preservation by default)
        assert _reduce_to_single(29) == 2

    def test_large_number(self):
        # 999 → 9+9+9=27 → 2+7=9
        assert _reduce_to_single(999) == 9


class TestChaldeanValues:
    """Test Chaldean letter mapping."""

    def test_a_equals_1(self):
        assert _chaldean_value("A") == 1
        assert _chaldean_value("a") == 1

    def test_h_equals_5(self):
        assert _chaldean_value("H") == 5

    def test_f_equals_8(self):
        assert _chaldean_value("F") == 8

    def test_o_equals_7(self):
        assert _chaldean_value("O") == 7

    def test_r_equals_2(self):
        assert _chaldean_value("R") == 2

    def test_s_equals_3(self):
        assert _chaldean_value("S") == 3

    def test_non_letter_returns_0(self):
        assert _chaldean_value(" ") == 0
        assert _chaldean_value("5") == 0
        assert _chaldean_value("-") == 0


class TestDestinyNumber:
    """Test destiny number (from birth date)."""

    def test_mumbai_1990(self):
        # 15+3+1990 digits: 1+5+3+1+9+9+0 = 28 → 2+8 = 10 → 1
        result = calculate_numerology("Test", 1990, 3, 15)
        assert result.destiny_number == 1

    def test_delhi_1992(self):
        # 5+1+1992 digits: 5+1+1+9+9+2 = 27 → 2+7 = 9
        result = calculate_numerology("Test", 1992, 1, 5)
        assert result.destiny_number == 9

    def test_jaipur_2005(self):
        # 10+4+2005 digits: 1+0+4+2+0+0+5 = 12 → 1+2 = 3
        result = calculate_numerology("Test", 2005, 4, 10)
        assert result.destiny_number == 3


class TestRadicalNumber:
    """Test radical number (birth day reduction)."""

    def test_born_on_15th(self):
        # 1+5 = 6
        result = calculate_numerology("Test", 1990, 1, 15)
        assert result.radical_number == 6

    def test_born_on_7th(self):
        result = calculate_numerology("Test", 1990, 1, 7)
        assert result.radical_number == 7

    def test_born_on_29th(self):
        # 2+9 = 11 → 1+1 = 2 (no master number preservation)
        result = calculate_numerology("Test", 1990, 1, 29)
        assert result.radical_number == 2


class TestNameNumber:
    """Test name number (Chaldean letter values)."""

    def test_rahul_sharma(self):
        # Chaldean: R=2,A=1,H=5,U=6,L=3=17; S=3,H=5,A=1,R=2,M=4,A=1=16
        # Total=33 → 3+3=6
        result = calculate_numerology("Rahul Sharma", 1990, 3, 15)
        assert result.name_number == 6

    def test_priya_patel(self):
        # Chaldean: P=8,R=2,I=1,Y=1,A=1=13; P=8,A=1,T=4,E=5,L=3=21
        # Total=34 → 3+4=7
        result = calculate_numerology("Priya Patel", 1992, 1, 5)
        assert result.name_number == 7

    def test_meera_iyer(self):
        # API confirmed: name_number=8
        result = calculate_numerology("Meera Iyer", 2005, 4, 10)
        assert result.name_number == 8


class TestEmptyNameHandling:
    """Test graceful handling of empty/invalid names."""

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="at least one letter"):
            calculate_numerology("", 1990, 1, 1)

    def test_only_spaces_raises(self):
        with pytest.raises(ValueError, match="at least one letter"):
            calculate_numerology("   ", 1990, 1, 1)

    def test_only_numbers_raises(self):
        with pytest.raises(ValueError, match="at least one letter"):
            calculate_numerology("12345", 1990, 1, 1)


class TestNameWithSpaces:
    """Test that spaces and non-letter characters are ignored."""

    def test_spaces_ignored(self):
        r1 = calculate_numerology("John Doe", 1990, 1, 1)
        r2 = calculate_numerology("JohnDoe", 1990, 1, 1)
        assert r1.name_number == r2.name_number

    def test_hyphens_ignored(self):
        r1 = calculate_numerology("Mary-Jane", 1990, 1, 1)
        r2 = calculate_numerology("MaryJane", 1990, 1, 1)
        assert r1.name_number == r2.name_number


class TestLuckyNumbers:
    """Test lucky numbers derivation."""

    def test_lucky_numbers_valid_range(self):
        result = calculate_numerology("Test", 1990, 1, 15)
        assert all(1 <= n <= 9 for n in result.lucky_numbers)

    def test_lucky_numbers_for_radical_6(self):
        # born on 15th → radical = 6
        result = calculate_numerology("Test", 1990, 1, 15)
        assert result.lucky_numbers == [3, 5, 6, 9]

    def test_evil_numbers_complement_lucky(self):
        result = calculate_numerology("Test", 1990, 1, 15)
        all_digits = set(range(1, 10))
        assert set(result.lucky_numbers) | set(result.evil_numbers) == all_digits
        assert set(result.lucky_numbers) & set(result.evil_numbers) == set()

    def test_lucky_numbers_for_radical_1(self):
        result = calculate_numerology("Test", 1990, 1, 1)
        assert result.lucky_numbers == [1, 2, 3, 9]


class TestNumerologyResult:
    """Test overall result structure."""

    def test_result_is_frozen(self):
        result = calculate_numerology("Test", 1990, 1, 15)
        with pytest.raises(Exception):
            result.name = "Changed"  # type: ignore

    def test_date_of_birth_format(self):
        result = calculate_numerology("Test", 1990, 3, 15)
        assert result.date_of_birth == "1990-03-15"

    def test_name_preserved(self):
        result = calculate_numerology("John Doe", 1990, 3, 15)
        assert result.name == "John Doe"


class TestAgainstAPI:
    """Cross-validate against AstrologyAPI.com numerology results."""

    @pytest.mark.parametrize("name,year,month,day,exp_destiny,exp_radical,exp_name", [
        ("Rahul Sharma", 1990, 3, 15, 1, 6, 6),
        ("Priya Patel", 1992, 1, 5, 9, 5, 7),
        ("Amit Kumar", 1985, 7, 4, 7, 4, 7),
        ("Deepika Singh", 2000, 11, 20, 6, 2, 7),
        ("Vikram Reddy", 1975, 12, 25, 5, 7, 5),
        ("Sneha Gupta", 1988, 8, 15, 4, 6, 5),
        ("Arjun Nair", 1995, 6, 21, 6, 3, 6),
        ("Meera Iyer", 2005, 4, 10, 3, 1, 8),
        ("Kiran Das", 1998, 9, 1, 1, 1, 1),
        ("Pooja Rao", 2010, 2, 14, 1, 5, 7),
    ])
    def test_api_match(self, name, year, month, day, exp_destiny, exp_radical, exp_name):
        result = calculate_numerology(name, year, month, day)
        assert result.destiny_number == exp_destiny, f"Destiny: got {result.destiny_number}, expected {exp_destiny}"
        assert result.radical_number == exp_radical, f"Radical: got {result.radical_number}, expected {exp_radical}"
        assert result.name_number == exp_name, f"Name: got {result.name_number}, expected {exp_name}"
