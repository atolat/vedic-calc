"""Tests for Ashtakoot Milan compatibility calculator."""

from vedic_calc.core.constants import Nakshatra, Sign
from vedic_calc.compatibility.calculator import calculate_compatibility


def test_same_person_compatibility():
    """Same nakshatra/sign should score high on most kuttas but 0 on Nadi."""
    result = calculate_compatibility(
        person1_nakshatra=Nakshatra.ROHINI,
        person1_sign=Sign.TAURUS,
        person2_nakshatra=Nakshatra.ROHINI,
        person2_sign=Sign.TAURUS,
    )
    assert result.total_score <= 36.0
    nadi = [k for k in result.kuttas if k.name == "Nadi"][0]
    assert nadi.obtained == 0.0
    maitri = [k for k in result.kuttas if k.name == "Graha Maitri"][0]
    assert maitri.obtained == 5.0
    vashya = [k for k in result.kuttas if k.name == "Vashya"][0]
    assert vashya.obtained == 2.0


def test_total_is_sum_of_kuttas():
    """Total score should equal sum of individual kutta scores."""
    result = calculate_compatibility(
        person1_nakshatra=Nakshatra.ASHWINI,
        person1_sign=Sign.ARIES,
        person2_nakshatra=Nakshatra.MAGHA,
        person2_sign=Sign.LEO,
    )
    assert result.total_score == sum(k.obtained for k in result.kuttas)
    assert len(result.kuttas) == 8


def test_all_kuttas_within_bounds():
    """Each kutta score should be between 0 and its maximum."""
    for nk1 in [Nakshatra.ASHWINI, Nakshatra.ROHINI, Nakshatra.PUSHYA, Nakshatra.MOOLA]:
        for nk2 in [Nakshatra.BHARANI, Nakshatra.HASTA, Nakshatra.JYESHTHA, Nakshatra.REVATI]:
            s1 = Sign(min((nk1 - 1) // 2 + 1, 12))
            s2 = Sign(min((nk2 - 1) // 2 + 1, 12))
            result = calculate_compatibility(nk1, s1, nk2, s2)
            for k in result.kuttas:
                assert 0.0 <= k.obtained <= k.maximum, f"{k.name}: {k.obtained} > {k.maximum}"
            assert 0.0 <= result.total_score <= 36.0


def test_nadi_dosha():
    """Same nadi nakshatras should get 0 for Nadi kutta."""
    # Ashwini and Ardra are both Aadi (Vata) nadi
    result = calculate_compatibility(
        person1_nakshatra=Nakshatra.ASHWINI,
        person1_sign=Sign.ARIES,
        person2_nakshatra=Nakshatra.ARDRA,
        person2_sign=Sign.GEMINI,
    )
    nadi = [k for k in result.kuttas if k.name == "Nadi"][0]
    assert nadi.obtained == 0.0
    assert "Nadi Dosha" in nadi.description


def test_different_nadi():
    """Different nadi should get full 8 points."""
    # Ashwini (Aadi) and Bharani (Madhya)
    result = calculate_compatibility(
        person1_nakshatra=Nakshatra.ASHWINI,
        person1_sign=Sign.ARIES,
        person2_nakshatra=Nakshatra.BHARANI,
        person2_sign=Sign.ARIES,
    )
    nadi = [k for k in result.kuttas if k.name == "Nadi"][0]
    assert nadi.obtained == 8.0


def test_verdict_thresholds():
    """Verify verdict text matches score ranges."""
    result = calculate_compatibility(
        person1_nakshatra=Nakshatra.ASHWINI,
        person1_sign=Sign.ARIES,
        person2_nakshatra=Nakshatra.BHARANI,
        person2_sign=Sign.ARIES,
    )
    if result.total_score >= 33:
        assert "Excellent" in result.verdict
    elif result.total_score >= 25:
        assert "Good" in result.verdict
    elif result.total_score >= 18:
        assert "Acceptable" in result.verdict
    else:
        assert "Not recommended" in result.verdict


def test_bhakoot_bad_pairs():
    """Signs in 6/8 relationship should get 0 for Bhakoot.

    Jyotish uses inclusive counting: Aries to Aries = 1st, Aries to Taurus = 2nd.
    Aries(1) to Virgo(6): inclusive = 6th from Aries, reverse = 8th. → {6,8} = bad.
    """
    result = calculate_compatibility(
        person1_nakshatra=Nakshatra.ASHWINI,
        person1_sign=Sign.ARIES,
        person2_nakshatra=Nakshatra.HASTA,
        person2_sign=Sign.VIRGO,
    )
    bhakoot = [k for k in result.kuttas if k.name == "Bhakoot"][0]
    assert bhakoot.obtained == 0.0

    # 2/12 pair: Aries(1) to Taurus(2) — 2nd from Aries, 12th from Taurus
    result2 = calculate_compatibility(
        person1_nakshatra=Nakshatra.ASHWINI,
        person1_sign=Sign.ARIES,
        person2_nakshatra=Nakshatra.ROHINI,
        person2_sign=Sign.TAURUS,
    )
    bhakoot2 = [k for k in result2.kuttas if k.name == "Bhakoot"][0]
    assert bhakoot2.obtained == 0.0


def test_bhakoot_good_pair():
    """Signs not in bad relationship should get full 7 for Bhakoot."""
    # Aries(1) to Gemini(3): 3rd from Aries, 11th from Gemini → not a bad pair
    result = calculate_compatibility(
        person1_nakshatra=Nakshatra.ASHWINI,
        person1_sign=Sign.ARIES,
        person2_nakshatra=Nakshatra.ARDRA,
        person2_sign=Sign.GEMINI,
    )
    bhakoot = [k for k in result.kuttas if k.name == "Bhakoot"][0]
    assert bhakoot.obtained == 7.0


def test_yoni_enemies():
    """Enemy yoni pairs should get 0 points."""
    # Ashwini = Horse, Swati = Buffalo — enemies
    result = calculate_compatibility(
        person1_nakshatra=Nakshatra.ASHWINI,
        person1_sign=Sign.ARIES,
        person2_nakshatra=Nakshatra.SWATI,
        person2_sign=Sign.LIBRA,
    )
    yoni = [k for k in result.kuttas if k.name == "Yoni"][0]
    assert yoni.obtained == 0.0


def test_json_serializable():
    """Result should be JSON serializable."""
    result = calculate_compatibility(
        person1_nakshatra=Nakshatra.ROHINI,
        person1_sign=Sign.TAURUS,
        person2_nakshatra=Nakshatra.HASTA,
        person2_sign=Sign.VIRGO,
    )
    json_str = result.model_dump_json()
    assert "total_score" in json_str
    assert "kuttas" in json_str
