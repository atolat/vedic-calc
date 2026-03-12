"""Comparison tests: vedic-calc muhurta vs PyJHora."""

import pytest

from vedic_calc.muhurta.calculator import calculate_muhurta
from .conftest import REFERENCE_CHARTS

pyjhora = pytest.importorskip("pyjhora", reason="PyJHora not installed")


def test_muhurta_matches_pyjhora(collector):
    vc_result = calculate_muhurta(2026, 3, 12, 19.076, 72.878, 5.5)
    pytest.skip("PyJHora API mapping not yet implemented")
