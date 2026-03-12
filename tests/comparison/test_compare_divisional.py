"""Comparison tests: vedic-calc divisional charts vs PyJHora."""

import pytest
import time

from vedic_calc.chart.divisional import calculate_divisional_chart
from vedic_calc.core.constants import Planet, Sign

from .conftest import REFERENCE_CHARTS, ComparisonRecord


pyjhora = pytest.importorskip("pyjhora", reason="PyJHora not installed")


@pytest.mark.parametrize("ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS])
@pytest.mark.parametrize("division", [9, 2, 3, 10, 12])
def test_divisional_matches_pyjhora(ref, division, collector):
    """Compare divisional chart signs with PyJHora."""
    vc_chart = ref.calculate()

    vc_start = time.perf_counter()
    vc_result = calculate_divisional_chart(vc_chart, division)
    vc_time = (time.perf_counter() - vc_start) * 1000

    # PyJHora equivalent call would go here
    # pj_result = pyjhora.divisional_chart(...)

    # Placeholder: skip actual comparison until PyJHora API is mapped
    pytest.skip("PyJHora API mapping not yet implemented")
