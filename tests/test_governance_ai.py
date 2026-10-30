from trading_ai.governance_ai import (
    build_deterministic_summary,
    build_drafting_evidence,
    validate_governance_ai_output,
)


EVIDENCE = {
    "issue_id": "DQ-001",
    "field": "trade_id",
    "rule": "Trade ID must be unique",
    "observed_pass_rate": 0.9917,
    "threshold": 1.0,
    "severity": "High",
    "status": "OPEN",
    "root_cause": "To be investigated",
    "remediation_action": (
        "Investigate duplicate records and determine "
        "whether the issue originates from source data "
        "or record-processing logic."
    ),
    "escalation_required": "YES",
    "data_owner_role": "Trading Operations",
    "data_steward_role": "Markets Data Steward",
    "business_definition": (
        "Unique identifier for each trade"
    ),
    "business_process": (
        "Trade Processing"
    ),
    "criticality": "Critical",
    "downstream_use": (
        "Record identification and trade-level analysis"
    ),
}


def _valid_draft() -> dict:
    return {
        "summary": (
            "The trade ID uniqueness control did not "
            "meet its required threshold."
        ),
        "business_context": (
            "Trade ID is the unique identifier for each trade "
            "within the Trade Processing process and is used "
            "for record identification and trade-level analysis."
        ),
        "root_cause_status": "UNCONFIRMED",
        "evidence_used": [
            "field",
            "business_definition",
            "business_process",
            "downstream_use",
        ],
        "requires_human_review": True,
    }


def test_valid_governance_ai_output_is_accepted():
    result = (
        validate_governance_ai_output(
            _valid_draft(),
            EVIDENCE,
        )
    )

    assert result["valid"] is True
    assert result["errors"] == []


def test_invented_root_cause_is_rejected():
    draft = _valid_draft()

    draft["summary"] = (
        "The uniqueness failure was caused by "
        "an upstream source-system defect."
    )

    result = (
        validate_governance_ai_output(
            draft,
            EVIDENCE,
        )
    )

    assert result["valid"] is False

    assert (
        "unsupported_root_cause_claim"
        in result["errors"]
    )


def test_changed_numeric_value_is_rejected():
    draft = _valid_draft()

    draft["summary"] = (
        "The observed pass rate was 0.95."
    )

    result = (
        validate_governance_ai_output(
            draft,
            EVIDENCE,
        )
    )

    assert result["valid"] is False

    assert (
        "unsupported_numeric_claim"
        in result["errors"]
    )


def test_changed_severity_is_rejected():
    draft = _valid_draft()

    draft["summary"] = (
        "This is a Medium severity "
        "data-quality issue."
    )

    result = (
        validate_governance_ai_output(
            draft,
            EVIDENCE,
        )
    )

    assert result["valid"] is False

    assert (
        "severity_mismatch"
        in result["errors"]
    )


def test_missing_human_review_is_rejected():
    draft = _valid_draft()

    draft[
        "requires_human_review"
    ] = False

    result = (
        validate_governance_ai_output(
            draft,
            EVIDENCE,
        )
    )

    assert result["valid"] is False

    assert (
        "human_review_not_required"
        in result["errors"]
    )


def test_unsupported_evidence_reference_is_rejected():
    draft = _valid_draft()

    draft["evidence_used"].append(
        "source_system_diagnosis"
    )

    result = (
        validate_governance_ai_output(
            draft,
            EVIDENCE,
        )
    )

    assert result["valid"] is False

    assert (
        "unsupported_evidence_reference"
        in result["errors"]
    )


def test_equivalent_percentage_representation_is_accepted():
    draft = _valid_draft()

    draft["summary"] = (
        "The observed pass rate was 99.17%, "
        "below the required threshold of 100%."
    )

    result = (
        validate_governance_ai_output(
            draft,
            EVIDENCE,
        )
    )

    assert result["valid"] is True


def test_number_from_authoritative_rule_is_accepted():
    draft = _valid_draft()

    draft["summary"] = (
        "The rule requires the value to be "
        "between 0 and the order quantity."
    )

    evidence = {
        **EVIDENCE,
        "rule": (
            "Executed quantity must be between "
            "0 and order quantity"
        ),
    }

    result = (
        validate_governance_ai_output(
            draft,
            evidence,
        )
    )

    assert result["valid"] is True


def test_duplicate_evidence_reference_is_rejected():
    draft = _valid_draft()

    draft["evidence_used"] = [
        "field",
        "business_definition",
        "downstream_use",
        "field",
    ]

    result = (
        validate_governance_ai_output(
            draft,
            EVIDENCE,
        )
    )

    assert result["valid"] is False

    assert (
        "duplicate_evidence_reference"
        in result["errors"]
    )


def test_drafting_evidence_is_minimised():
    result = (
        build_drafting_evidence(
            EVIDENCE
        )
    )

    assert set(result) == {
        "field",
        "business_definition",
        "business_process",
        "downstream_use",
    }

    assert "rule" not in result
    assert (
        "observed_pass_rate"
        not in result
    )
    assert "threshold" not in result
    assert "severity" not in result
    assert "root_cause" not in result
    assert (
        "remediation_action"
        not in result
    )


def test_deterministic_summary_marks_below_threshold_as_fail():
    summary = (
        build_deterministic_summary(
            EVIDENCE
        )
    )

    assert "0.9917" in summary
    assert "1.0" in summary
    assert "is below" in summary
    assert (
        "control status: FAIL"
        in summary
    )


def test_deterministic_summary_handles_dq002_relation_correctly():
    evidence = {
        **EVIDENCE,
        "rule": (
            "Executed quantity must be between "
            "0 and order quantity"
        ),
        "observed_pass_rate": 0.9958,
        "threshold": 1.0,
    }

    summary = (
        build_deterministic_summary(
            evidence
        )
    )

    assert "0.9958" in summary
    assert "1.0" in summary
    assert "is below" in summary

    assert (
        "control status: FAIL"
        in summary
    )

    assert "above" not in summary


def test_deterministic_summary_marks_threshold_as_pass():
    evidence = {
        **EVIDENCE,
        "observed_pass_rate": 1.0,
        "threshold": 1.0,
    }

    summary = (
        build_deterministic_summary(
            evidence
        )
    )

    assert (
        "meets or exceeds"
        in summary
    )

    assert (
        "control status: PASS"
        in summary
    )