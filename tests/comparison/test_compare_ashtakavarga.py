"""Comparison tests: vedic-calc Ashtakavarga vs PyJHora."""

import pytest

from vedic_calc.strength.ashtakavarga import calculate_ashtakavarga
from .conftest import REFERENCE_CHARTS

pyjhora = pytest.importorskip("pyjhora", reason="PyJHora not installed")


@pytest.mark.parametrize("ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS])
def test_ashtakavarga_matches_pyjhora(ref, collector):
    vc_chart = ref.calculate()
    vc_result = calculate_ashtakavarga(vc_chart)
    pytest.skip("PyJHora API mapping not yet implemented")
