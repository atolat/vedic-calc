"""Comparison tests: vedic-calc dashas vs PyJHora."""

import pytest

from vedic_calc.dasha.calculator import calculate_dasha
from vedic_calc.dasha.yogini import calculate_yogini_dasha
from vedic_calc.dasha.ashtottari import calculate_ashtottari_dasha
from .conftest import REFERENCE_CHARTS

pyjhora = pytest.importorskip("pyjhora", reason="PyJHora not installed")


@pytest.mark.parametrize("ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS])
def test_vimsottari_matches_pyjhora(ref, collector):
    vc_chart = ref.calculate()
    vc_result = calculate_dasha(vc_chart, levels=1)
    pytest.skip("PyJHora API mapping not yet implemented")


@pytest.mark.parametrize("ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS])
def test_yogini_matches_pyjhora(ref, collector):
    vc_chart = ref.calculate()
    vc_result = calculate_yogini_dasha(vc_chart, levels=1)
    pytest.skip("PyJHora API mapping not yet implemented")
