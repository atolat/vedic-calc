"""
Upagraha (sub-planet) position calculator.

Upagrahas are mathematically derived points — not physical celestial bodies.
They are computed from planetary longitudes using fixed arithmetic formulas
described in classical texts. Despite being "virtual", they are used in
Vedic astrology to refine predictions about specific life areas.

THE FIVE SUN-BASED UPAGRAHAS (from BPHS Ch. 25):
    These form a chain, each derived from the previous one:

    1. Dhuma       = Sun + 133°20'           (smoke of the Sun)
    2. Vyatipata   = 360° - Dhuma            (calamity point)
    3. Parivesha   = Vyatipata + 180°         (halo around Sun)
    4. Indrachapa  = 360° - Parivesha         (Indra's bow / rainbow)
    5. Upaketu     = Indrachapa + 16°40'      (comet / sub-Ketu)

    All values are taken modulo 360° to stay in the 0-360 range.

    Notice the elegant symmetry: Dhuma and Vyatipata are reflections
    around 180°, as are Parivesha and Indrachapa. Upaketu then adds
    a small fixed offset.

GULIKA AND MANDI:
    These depend on sunrise/sunset times and the weekday, requiring
    ephemeris calls. They are NOT computed here — a future module
    will handle them once sunrise data is readily available in
    the chart pipeline.

SOURCE REFERENCES:
    - Brihat Parashara Hora Shastra (BPHS), Ch. 25
    - Uttara Kalamrita, Ch. 4

Example:
    >>> from vedic_calc.chart.upagrahas import calculate_upagrahas
    >>> upagrahas = calculate_upagrahas(chart)
    >>> for u in upagrahas:
    ...     print(f"{u.name}: {u.degree_in_sign:.2f}° {u.sign.name}")
"""

from __future__ import annotations

from vedic_calc.chart.calculator import longitude_to_degree_in_sign, longitude_to_sign
from vedic_calc.core.constants import Planet
from vedic_calc.core.types import BirthChart, UpagrahaPosition


def calculate_upagrahas(chart: BirthChart) -> list[UpagrahaPosition]:
    """Calculate the five Sun-based upagraha positions.

    Each upagraha is derived from the Sun's sidereal longitude using
    fixed arithmetic (addition, subtraction, modulo 360). The chain is:

        Sun → Dhuma → Vyatipata → Parivesha → Indrachapa → Upaketu

    Args:
        chart: A complete BirthChart with planetary positions.

    Returns:
        A list of 5 UpagrahaPosition objects in chain order:
        [Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu].
    """
    sun_lon = chart.planets[Planet.SUN].longitude

    # --- Dhuma: Sun + 133°20' (= 133.333°) ---
    dhuma_lon = (sun_lon + 133.0 + 20.0 / 60.0) % 360.0

    # --- Vyatipata: 360° - Dhuma ---
    vyatipata_lon = (360.0 - dhuma_lon) % 360.0

    # --- Parivesha: Vyatipata + 180° ---
    parivesha_lon = (vyatipata_lon + 180.0) % 360.0

    # --- Indrachapa: 360° - Parivesha ---
    indrachapa_lon = (360.0 - parivesha_lon) % 360.0

    # --- Upaketu: Indrachapa + 16°40' (= 16.667°) ---
    upaketu_lon = (indrachapa_lon + 16.0 + 40.0 / 60.0) % 360.0

    # Build UpagrahaPosition objects for each
    entries = [
        ("Dhuma", dhuma_lon),
        ("Vyatipata", vyatipata_lon),
        ("Parivesha", parivesha_lon),
        ("Indrachapa", indrachapa_lon),
        ("Upaketu", upaketu_lon),
    ]

    results: list[UpagrahaPosition] = []
    for name, lon in entries:
        results.append(
            UpagrahaPosition(
                name=name,
                longitude=round(lon, 4),
                sign=longitude_to_sign(lon),
                degree_in_sign=round(longitude_to_degree_in_sign(lon), 4),
            )
        )

    return results
