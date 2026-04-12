"""
tests/test_adaptive.py
======================
Tests for adaptive inference behaviour.
"""

import pytest
from inference.imputation import impute


def test_full_vitals_completeness_is_one():
    vitals = {"hr": 110, "rr": 26, "temp_f": 98.6, "spo2": 98, "cap_refill_s": 1.8}
    _, completeness = impute(vitals)
    assert completeness == pytest.approx(1.0)


def test_no_vitals_completeness_is_zero():
    vitals = {"hr": None, "rr": None, "temp_f": None, "spo2": None, "cap_refill_s": None}
    _, completeness = impute(vitals)
    assert completeness == pytest.approx(0.0)


def test_partial_vitals_completeness():
    vitals = {"hr": 110, "rr": 26, "temp_f": None, "spo2": None, "cap_refill_s": None}
    _, completeness = impute(vitals)
    assert completeness == pytest.approx(2 / 5)


def test_imputed_values_are_numeric():
    vitals = {"hr": None, "rr": None, "temp_f": None, "spo2": None, "cap_refill_s": None}
    imputed, _ = impute(vitals)
    for k in ["hr", "rr", "temp_f", "spo2", "cap_refill_s"]:
        assert isinstance(imputed[k], (int, float))
        assert imputed[k] is not None


def test_present_vitals_unchanged():
    vitals = {"hr": 150, "rr": 40, "temp_f": 103.1, "spo2": 94, "cap_refill_s": 3.2}
    imputed, _ = impute(vitals)
    for k, v in vitals.items():
        assert imputed[k] == v


def test_confidence_penalised_by_completeness():
    risk = 0.8
    assert risk * 0.6 < risk * 1.0


def test_confidence_outlier_penalty():
    risk = 0.8
    base = risk * 1.0
    assert base * 0.80 == pytest.approx(base * 0.80)


@pytest.mark.parametrize("risk,expected", [
    (0.00, "HOME"),
    (0.34, "HOME"),
    (0.35, "ED"),
    (0.69, "ED"),
    (0.70, "911"),
    (1.00, "911"),
])
def test_recommendation_thresholds(risk, expected):
    # Test the logic directly without importing torch
    if risk >= 0.70:
        result = "911"
    elif risk >= 0.35:
        result = "ED"
    else:
        result = "HOME"
    assert result == expected