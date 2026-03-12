"""Tests for Muhurta calculations."""

import pytest
from datetime import datetime

from vedic_calc.muhurta.calculator import calculate_muhurta


class TestMuhurtaStructure:
    def test_returns_muhurta_info(self):
        result = calculate_muhurta(2026, 3, 12, 19.076, 72.878, 5.5)
        assert result is not None
        assert hasattr(result, "rahu_kalam")
        assert hasattr(result, "yamagandam")
        assert hasattr(result, "gulika_kalam")
        assert hasattr(result, "abhijit_muhurta")
        assert hasattr(result, "choghadiya_day")
        assert hasattr(result, "choghadiya_night")
        assert hasattr(result, "hora")

    def test_rahu_kalam_order(self):
        result = calculate_muhurta(2026, 3, 12, 19.076, 72.878, 5.5)
        start, end = result.rahu_kalam
        assert start < end

    def test_abhijit_around_noon(self):
        result = calculate_muhurta(2026, 3, 12, 19.076, 72.878, 5.5)
        start, end = result.abhijit_muhurta
        # Abhijit should be around noon (11-13 hours)
        assert 10 <= start.hour <= 13
        assert 11 <= end.hour <= 14

    def test_choghadiya_count(self):
        result = calculate_muhurta(2026, 3, 12, 19.076, 72.878, 5.5)
        assert len(result.choghadiya_day) == 8
        assert len(result.choghadiya_night) == 8

    def test_choghadiya_quality(self):
        result = calculate_muhurta(2026, 3, 12, 19.076, 72.878, 5.5)
        valid_qualities = {"good", "best", "bad"}
        for name, start, end, quality in result.choghadiya_day:
            assert quality in valid_qualities, f"Invalid quality: {quality}"
