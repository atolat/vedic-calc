"""Comparison tests: vedic-calc yogas vs PyJHora."""

import pytest

from vedic_calc.yoga.calculator import detect_yogas
from .conftest import REFERENCE_CHARTS

pyjhora = pytest.importorskip("pyjhora", reason="PyJHora not installed")


@pytest.mark.parametrize("ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS])
def test_yogas_match_pyjhora(ref, collector):
    vc_chart = ref.calculate()
    vc_result = detect_yogas(vc_chart)
    pytest.skip("PyJHora API mapping not yet implemented")
