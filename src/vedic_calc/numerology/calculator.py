"""Numerology calculator using Chaldean and Vedic numerology systems.

Calculates destiny number (from birth date), radical number (from birth day),
name number (Chaldean letter values), lucky numbers, evil numbers, and
personal year from a person's name and birth date.

CHALDEAN MAPPING (used for name number):
    A=1, B=2, C=3, D=4, E=5, F=8, G=3, H=5, I=1
    J=1, K=2, L=3, M=4, N=5, O=7, P=8, Q=1, R=2
    S=3, T=4, U=6, V=6, W=6, X=5, Y=1, Z=7

DESTINY NUMBER: Sum of all digits in the full birth date (day+month+year).
RADICAL NUMBER: Sum of the birth day digits.
NAME NUMBER: Sum of Chaldean letter values of the full name.

MASTER NUMBERS:
    11, 22, and 33 are considered "master numbers" and are NOT reduced
    further when encountered during digit reduction.
"""

from __future__ import annotations

from datetime import date

from vedic_calc.core.types import NumerologyResult

MASTER_NUMBERS = frozenset({11, 22, 33})

# Whether to preserve master numbers during reduction.
# Standard Indian numerology (as used by most APIs) does NOT preserve them.
_PRESERVE_MASTERS = False

# Chaldean letter-to-number mapping
_CHALDEAN: dict[str, int] = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 8, "G": 3, "H": 5, "I": 1,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "O": 7, "P": 8, "Q": 1, "R": 2,
    "S": 3, "T": 4, "U": 6, "V": 6, "W": 6, "X": 5, "Y": 1, "Z": 7,
}

# Lucky numbers for each radical number (1-9).
_LUCKY_MAP: dict[int, list[int]] = {
    1: [1, 2, 3, 9],
    2: [1, 2, 5, 6],
    3: [1, 3, 5, 6, 9],
    4: [1, 4, 5, 6, 7],
    5: [1, 4, 5, 6, 9],
    6: [3, 5, 6, 9],
    7: [1, 4, 5, 6, 7],
    8: [1, 5, 6, 8],
    9: [1, 3, 5, 6, 9],
}

# Evil (unfavorable) numbers: digits 1-9 that are NOT lucky for a given radical.
_EVIL_MAP: dict[int, list[int]] = {
    k: sorted(set(range(1, 10)) - set(v)) for k, v in _LUCKY_MAP.items()
}


def _reduce_to_single(n: int) -> int:
    """Reduce a number by summing its digits until a single digit or master number.

    Master numbers (11, 22, 33) are preserved and not reduced further.

    Examples:
        >>> _reduce_to_single(29)   # 2+9=11 → master number, keep
        11
        >>> _reduce_to_single(28)   # 2+8=10 → 1+0=1
        1
        >>> _reduce_to_single(38)   # 3+8=11 → master number, keep
        11
        >>> _reduce_to_single(5)    # already single digit
        5
    """
    if _PRESERVE_MASTERS:
        while n > 9 and n not in MASTER_NUMBERS:
            n = sum(int(d) for d in str(n))
    else:
        while n > 9:
            n = sum(int(d) for d in str(n))
    return n


def _chaldean_value(ch: str) -> int:
    """Return the Chaldean numerology value for a letter.

    Only ASCII letters A-Z are mapped. Non-letter characters return 0.
    """
    return _CHALDEAN.get(ch.upper(), 0)


def _name_to_chaldean_sum(name: str) -> int:
    """Sum all Chaldean letter values in a name string."""
    return sum(_chaldean_value(ch) for ch in name)


def _date_digit_sum(year: int, month: int, day: int) -> int:
    """Sum all digits in a date (day + month + year)."""
    date_str = f"{day}{month}{year}"
    return sum(int(d) for d in date_str)


def calculate_numerology(
    name: str,
    year: int,
    month: int,
    day: int,
) -> NumerologyResult:
    """Calculate numerological numbers from name and birth date.

    Args:
        name: Full name (spaces and non-letter characters are ignored).
        year: Birth year (e.g. 1990).
        month: Birth month (1-12).
        day: Birth day (1-31).

    Returns:
        NumerologyResult with all computed numerological numbers.

    Raises:
        ValueError: If name contains no letters or date is invalid.

    Example:
        >>> result = calculate_numerology("John Doe", 1990, 3, 15)
        >>> result.radical_number
        6
    """
    # Validate
    letters_only = [ch for ch in name if ch.isalpha()]
    if not letters_only:
        raise ValueError("Name must contain at least one letter.")
    # Validate date
    birth_date = date(year, month, day)  # raises ValueError if invalid

    # Destiny number: sum of all digits in birth date (day+month+year), reduced.
    destiny_number = _reduce_to_single(_date_digit_sum(year, month, day))

    # Radical number: sum of birth day digits, reduced.
    radical_number = _reduce_to_single(day)

    # Name number: sum of Chaldean letter values in name, reduced.
    name_number = _reduce_to_single(_name_to_chaldean_sum(name))

    # Lucky and evil numbers based on radical number.
    # For master numbers (11, 22, 33), use the reduced single digit for lookup.
    radical_key = _reduce_to_single(sum(int(d) for d in str(radical_number))) if radical_number > 9 else radical_number
    lucky_numbers = _LUCKY_MAP[radical_key]
    evil_numbers = _EVIL_MAP[radical_key]

    # Personal year: (birth_day + birth_month + current_year) reduced.
    current_year = date.today().year
    personal_year = _reduce_to_single(day + month + current_year)

    return NumerologyResult(
        name=name,
        date_of_birth=birth_date.isoformat(),
        destiny_number=destiny_number,
        radical_number=radical_number,
        name_number=name_number,
        lucky_numbers=lucky_numbers,
        evil_numbers=evil_numbers,
        personal_year=personal_year,
    )
