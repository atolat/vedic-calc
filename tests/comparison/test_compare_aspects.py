"""Comparison tests: vedic-calc aspects vs PyJHora."""

import pytest

from vedic_calc.chart.aspects import calculate_aspects
from .conftest import REFERENCE_CHARTS

pyjhora = pytest.importorskip("pyjhora", reason="PyJHora not installed")


@pytest.mark.parametrize("ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS])
def test_aspects_match_pyjhora(ref, collector):
    vc_chart = ref.calculate()
    vc_result = calculate_aspects(vc_chart)
    pytest.skip("PyJHora API mapping not yet implemented")
