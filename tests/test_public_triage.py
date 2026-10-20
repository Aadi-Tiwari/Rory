from copy import deepcopy
import math

import pytest

from backend_a.validation.public_triage import STUDY, make_report, prepare_rows, read_cohort, run


@pytest.fixture
def source_row():
    return {
        "admitted": "1", "age_years": "1", "age_mths": "2", "age_days": "15",
        "pulse_rate": "110", "resp_rate": "28", "temp": "37", "oxygen_sat": "98",
        "cap_refill_cat": "5", "data_resuscitation": "1",
        "outcome": "2", "readmitted": "1",
    }


def test_source_units_and_missing_modalities(source_row):
    rows, _ = prepare_rows([source_row])
    row = rows[0]
    assert row["age_months"] == pytest.approx(14.5)
    assert row["vitals"]["temp_f"]["value"] == pytest.approx(98.6)
    assert row["vitals"]["cap_refill_s"] is None
    assert row["complaint"]["value"] == ""
    assert row["resuscitation_code"] == "1"


def test_later_outcomes_and_category_codes_do_not_change_inputs(source_row):
    altered = deepcopy(source_row)
    altered.update(outcome="1", readmitted="0", admitted="0", cap_refill_cat="1")
    first, _ = prepare_rows([source_row])
    second, _ = prepare_rows([altered])
    assert first[0]["vitals"] == second[0]["vitals"]
    assert first[0]["complaint"] == second[0]["complaint"]
    assert first[0]["admitted"] != second[0]["admitted"]


def test_age_components_and_boundaries(source_row):
    rows = []
    for years, months, days in [("", "2", ""), ("5", "", ""),
                                 ("", "1", "29"), ("5", "", "1"), ("", "", "")]:
        rows.append({**source_row, "age_years": years, "age_mths": months, "age_days": days})
    selected, flow = prepare_rows(rows)
    assert [row["age_months"] for row in selected] == [2, 60]
    assert flow["exclusions_in_applied_order"] == {"outside_age_range": 2, "missing_age": 1}


def test_exclusions_and_duplicate_accounting(source_row):
    missing_label = {**source_row, "admitted": ""}
    missing_vitals = {**source_row, **{key: "" for key in ("pulse_rate", "resp_rate", "temp", "oxygen_sat")}}
    rows, flow = prepare_rows([source_row, source_row.copy(), missing_label, missing_vitals])
    assert len(rows) == 1
    assert flow["released_rows"] == flow["included_rows"] + sum(flow["exclusions_in_applied_order"].values())
    assert flow["exclusions_in_applied_order"] == {
        "exact_duplicate_row": 1, "missing_or_unknown_admission": 1, "all_model_vitals_missing": 1,
    }


def test_missing_vital_is_not_filled_from_other_fields(source_row):
    source_row.update(pulse_rate="", outcome="217")
    rows, _ = prepare_rows([source_row])
    assert rows[0]["vitals"]["hr"] is None


def test_uninspected_release_rejected(tmp_path):
    path = tmp_path / "changed.csv"
    path.write_text("admitted\n1\n")
    with pytest.raises(ValueError, match="differs"):
        read_cohort(path)


def test_output_collision_rejected_before_reading_inputs(tmp_path):
    destination = tmp_path / "same.json"
    with pytest.raises(ValueError, match="distinct output paths"):
        run(tmp_path / "absent-manifest.json", tmp_path / "absent.csv", destination, destination)
    assert not destination.exists()


@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])
def test_nonfinite_vital_rejected(source_row, value):
    source_row["pulse_rate"] = value
    with pytest.raises(ValueError, match="Nonfinite"):
        prepare_rows([source_row])


def test_report_thresholds_and_age_partition(source_row, monkeypatch):
    monkeypatch.setitem(STUDY, "resamples", 2)
    source_rows = [
        {**source_row, "age_years": "", "age_mths": "2", "age_days": "", "admitted": "1"},
        {**source_row, "age_years": "1", "age_mths": "", "age_days": "", "admitted": "0"},
        {**source_row, "age_years": "2", "age_mths": "", "age_days": "", "admitted": "1"},
        {**source_row, "age_years": "5", "age_mths": "", "age_days": "", "admitted": "0"},
    ]
    rows, _ = prepare_rows(source_rows)
    report = make_report(rows, [[.8, .2, 0], [.6, 0, .4], [.1, .2, .7], [0, .2, .8]])
    assert report["overall_at_070"]["confusion"] == {"tp": 1, "fn": 1, "fp": 1, "tn": 1}
    assert report["overall_at_035"]["confusion"] == {"tp": 1, "fn": 1, "fp": 2, "tn": 0}
    assert sum(group["n"] for group in report["age_groups_months_at_070"].values()) == len(rows)
    assert report["overall_at_070"]["missing_vitals"]["cap_refill_s"] == len(rows)
    assert report["clinical_validation"] is False
    assert report["threshold_bands"] == {"below_035": 1, "035_to_070": 1, "at_least_070": 2}


def test_public_report_uses_service_policy_at_thresholds(source_row, monkeypatch):
    monkeypatch.setitem(STUDY, "resamples", 2)
    rows, _ = prepare_rows([source_row])
    lower = make_report(rows, [[.65, 0, .35]])
    assert lower["overall_at_035"]["confusion"]["tp"] == 1
    upper = make_report(rows, [[.29975, .0005, .69975]])
    assert upper["overall_at_070"]["confusion"]["tp"] == 1


@pytest.mark.parametrize("probabilities", [[], [[.5, .5]], [[0, 0, math.nan]], [[.8, .8, .8]]])
def test_invalid_probabilities_rejected(source_row, probabilities):
    rows, _ = prepare_rows([source_row])
    with pytest.raises(ValueError, match="Invalid"):
        make_report(rows, probabilities)
