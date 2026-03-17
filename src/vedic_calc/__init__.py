"""
vedic-calc: Open-source Vedic astrology calculation library.

Built on the Swiss Ephemeris (pyswisseph) for precise astronomical calculations,
with a clean Pythonic API using Pydantic models.

Quick start:
    >>> from vedic_calc import calculate_chart
    >>> chart = calculate_chart(
    ...     year=1990, month=3, day=15,
    ...     hour=10, minute=30,
    ...     latitude=19.0760, longitude=72.8777,  # Mumbai
    ...     timezone_offset=5.5,  # IST
    ... )
    >>> print(chart.ascendant.sign)
    <Sign.GEMINI: 3>

    >>> from vedic_calc import calculate_dasha
    >>> periods = calculate_dasha(chart)
    >>> periods[0].lord  # First mahadasha planet
    <Planet.MOON: 1>

    >>> from vedic_calc import calculate_panchanga
    >>> p = calculate_panchanga(2026, 3, 8, 19.076, 72.878, 5.5)
    >>> p.tithi_name
    'Shukla Dashami'

    >>> from vedic_calc import render_south_indian
    >>> print(render_south_indian(chart))
    ... (ASCII chart)
"""

from vedic_calc.core.types import (
    ArudhaPada,
    AshtakavargaResult,
    AspectInfo,
    BirthChart,
    CharaKaraka,
    CombustionStatus,
    DashaPeriod,
    DivisionalChart,
    DoshaResult,
    FestivalInfo,
    HouseAnalysis,
    KPChartResult,
    KPHouseCusp,
    KPPlanetInfo,
    KPSublordInfo,
    MuhurtaInfo,
    MuhurtaSearchResult,
    MuhurtaWindow,
    MunthaInfo,
    NakshatraInfo,
    NumerologyResult,
    PanchangaInfo,
    PlanetPosition,
    PlanetState,
    PoruthamResult,
    PrashnaVerdict,
    SahamPosition,
    ShadbalaResult,
    SpecialLagna,
    TajikaYoga,
    TransitChart,
    UpagrahaPosition,
    VarshaphalResult,
    YogaResult,
)
from vedic_calc.chart.calculator import calculate_chart
from vedic_calc.chart.renderer import render_north_indian, render_south_indian, render_svg
from vedic_calc.chart.divisional import calculate_divisional_chart
from vedic_calc.chart.aspects import calculate_aspects
from vedic_calc.chart.combustion import calculate_combustion
from vedic_calc.chart.states import calculate_planet_states
from vedic_calc.chart.transits import calculate_transit_chart
from vedic_calc.chart.houses import analyze_houses
from vedic_calc.chart.upagrahas import calculate_upagrahas
from vedic_calc.chart.special_lagnas import calculate_special_lagnas
from vedic_calc.chart.sahams import calculate_sahams
from vedic_calc.dasha.calculator import calculate_dasha, get_current_dasha
from vedic_calc.dasha.yogini import calculate_yogini_dasha
from vedic_calc.dasha.ashtottari import calculate_ashtottari_dasha
from vedic_calc.dasha.narayana import calculate_narayana_dasha
from vedic_calc.panchanga.calculator import calculate_panchanga
from vedic_calc.panchanga.festivals import get_festivals
from vedic_calc.compatibility.calculator import calculate_compatibility, CompatibilityResult
from vedic_calc.compatibility.porutham import calculate_porutham
from vedic_calc.yoga.calculator import detect_yogas
from vedic_calc.dosha.calculator import detect_doshas
from vedic_calc.muhurta.calculator import calculate_muhurta
from vedic_calc.muhurta.solver import find_muhurta_windows
from vedic_calc.prashna.chart import cast_prashna_chart
from vedic_calc.prashna.tajika import detect_tajika_yogas
from vedic_calc.prashna.evaluator import evaluate_prashna
from vedic_calc.jaimini.karakas import calculate_chara_karakas
from vedic_calc.jaimini.arudha import calculate_arudha_padas
from vedic_calc.strength.ashtakavarga import calculate_ashtakavarga
from vedic_calc.strength.shadbala import calculate_shadbala
from vedic_calc.varshaphal.calculator import calculate_varshaphal
from vedic_calc.kp.calculator import calculate_kp_chart
from vedic_calc.kp.sublords import get_kp_sublord
from vedic_calc.numerology.calculator import calculate_numerology
