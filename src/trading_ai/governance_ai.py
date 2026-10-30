from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

from .governance import build_governance_evidence
from .llm import generate_governance_issue_draft


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CDA_REGISTRY_PATH = (
    PROJECT_ROOT
    / "docs"
    / "cda_registry.csv"
)

ISSUE_REGISTER_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "governance_issue_register.csv"
)


ALLOWED_EVIDENCE_FIELDS = {
    "field",
    "business_definition",
    "business_process",
    "downstream_use",
}


UNSUPPORTED_CAUSAL_PATTERNS = [
    r"\bcaused by\b",
    r"\bdue to\b",
    r"\bresulted from\b",
    r"\bresulting from\b",
    r"\boriginated from\b",
    r"\boriginates from\b",
    r"\bbecause of\b",
]


def _extract_numbers(
    text: str,
) -> list[tuple[float, bool]]:
    """
    Extract numeric claims from text.

    Returns:
        A list of tuples:
        (numeric_value, is_percentage)
    """
    matches = re.findall(
        r"\b(\d+(?:\.\d+)?)\s*(%)?",
        text,
    )

    return [
        (float(value), percent == "%")
        for value, percent in matches
    ]


def _normalised_numeric_value(
    value: float,
    is_percentage: bool,
) -> float:
    """
    Convert percentages into decimal form.

    Example:
        99.17% -> 0.9917
    """
    if is_percentage:
        return value / 100.0

    return value


def _supported_numeric_values(
    evidence: dict,
) -> list[float]:
    """
    Build the set of numeric values explicitly supported
    by the complete authoritative governance evidence.
    """
    values: list[float] = []

    for field in (
        "observed_pass_rate",
        "threshold",
    ):
        if field in evidence:
            values.append(
                float(evidence[field])
            )

    textual_fields = (
        "field",
        "rule",
        "business_definition",
        "business_process",
        "downstream_use",
        "remediation_action",
    )

    for field in textual_fields:
        text = str(
            evidence.get(
                field,
                "",
            )
        )

        for (
            value,
            is_percentage,
        ) in _extract_numbers(text):
            values.append(
                _normalised_numeric_value(
                    value,
                    is_percentage,
                )
            )

    return values


def _number_is_supported(
    value: float,
    is_percentage: bool,
    supported_values: list[float],
    tolerance: float = 0.0001,
) -> bool:
    """
    Determine whether a numeric claim corresponds
    to authoritative evidence.
    """
    normalised = (
        _normalised_numeric_value(
            value,
            is_percentage,
        )
    )

    return any(
        abs(normalised - supported)
        <= tolerance
        for supported in supported_values
    )


def build_drafting_evidence(
    evidence: dict,
) -> dict:
    """
    Restrict the LLM to business-context evidence only.

    Deterministic governance facts such as pass rate,
    threshold, severity, remediation and issue status
    remain outside the generative drafting step.
    """
    allowed_fields = (
        "field",
        "business_definition",
        "business_process",
        "downstream_use",
    )

    return {
        field: evidence[field]
        for field in allowed_fields
        if field in evidence
    }


def _format_rate(
    value: float,
) -> str:
    """
    Format a governance rate consistently.

    Examples:
        0.9917 -> "0.9917"
        1.0    -> "1.0"
        0.9800 -> "0.98"
    """
    text = (
        f"{float(value):.4f}"
        .rstrip("0")
        .rstrip(".")
    )

    if "." not in text:
        text += ".0"

    return text


def build_deterministic_summary(
    evidence: dict,
) -> str:
    """
    Build the governance control summary deterministically.

    The LLM is deliberately not allowed to calculate
    or describe the relationship between the observed
    pass rate and the required threshold.
    """
    rule = str(
        evidence["rule"]
    )

    observed = float(
        evidence["observed_pass_rate"]
    )

    threshold = float(
        evidence["threshold"]
    )

    observed_text = _format_rate(
        observed
    )

    threshold_text = _format_rate(
        threshold
    )

    if observed >= threshold:
        relation = "meets or exceeds"
        control_status = "PASS"

    else:
        relation = "is below"
        control_status = "FAIL"

    return (
        f"Control rule: {rule}. "
        f"Observed pass rate: {observed_text}. "
        f"Required threshold: {threshold_text}. "
        f"The observed pass rate {relation} "
        f"the required threshold; "
        f"control status: {control_status}."
    )


def validate_governance_ai_output(
    draft: dict,
    evidence: dict,
) -> dict:
    """
    Validate the final governance draft
    against authoritative deterministic evidence.

    This is a runtime guardrail.

    It is intentionally not an LLM-based evaluator.
    """
    errors: list[str] = []

    required_fields = {
        "summary",
        "business_context",
        "root_cause_status",
        "evidence_used",
        "requires_human_review",
    }

    missing_fields = (
        required_fields
        - set(draft)
    )

    if missing_fields:
        errors.append(
            "missing_required_fields"
        )

    if (
        draft.get("root_cause_status")
        != "UNCONFIRMED"
    ):
        errors.append(
            "root_cause_status_changed"
        )

    if (
        draft.get("requires_human_review")
        is not True
    ):
        errors.append(
            "human_review_not_required"
        )

    evidence_used = draft.get(
        "evidence_used",
        [],
    )

    if not isinstance(
        evidence_used,
        list,
    ):
        errors.append(
            "evidence_used_not_list"
        )

    else:
        if len(evidence_used) != len(
            set(evidence_used)
        ):
            errors.append(
                "duplicate_evidence_reference"
            )

        unsupported_evidence = (
            set(evidence_used)
            - ALLOWED_EVIDENCE_FIELDS
        )

        if unsupported_evidence:
            errors.append(
                "unsupported_evidence_reference"
            )

    summary = str(
        draft.get(
            "summary",
            "",
        )
    )

    business_context = str(
        draft.get(
            "business_context",
            "",
        )
    )

    combined_text = (
        summary
        + " "
        + business_context
    ).strip()

    if not summary:
        errors.append(
            "empty_summary"
        )

    if not business_context:
        errors.append(
            "empty_business_context"
        )

    if (
        str(
            evidence.get(
                "root_cause",
                "",
            )
        ).lower()
        == "to be investigated"
    ):
        for pattern in (
            UNSUPPORTED_CAUSAL_PATTERNS
        ):
            if re.search(
                pattern,
                combined_text,
                flags=re.IGNORECASE,
            ):
                errors.append(
                    "unsupported_root_cause_claim"
                )
                break

    authoritative_severity = str(
        evidence.get(
            "severity",
            "",
        )
    ).lower()

    for severity in (
        "low",
        "medium",
        "high",
    ):
        if re.search(
            rf"\b{severity}\b",
            combined_text,
            flags=re.IGNORECASE,
        ):
            if (
                severity
                != authoritative_severity
            ):
                errors.append(
                    "severity_mismatch"
                )

            break

    supported_values = (
        _supported_numeric_values(
            evidence
        )
    )

    numeric_claims = (
        _extract_numbers(
            combined_text
        )
    )

    for (
        value,
        is_percentage,
    ) in numeric_claims:
        if not _number_is_supported(
            value,
            is_percentage,
            supported_values,
        ):
            errors.append(
                "unsupported_numeric_claim"
            )
            break

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def load_governance_artifacts() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:
    """
    Load the CDA registry and governance issue register.
    """
    cda_registry = pd.read_csv(
        CDA_REGISTRY_PATH
    )

    issue_register = pd.read_csv(
        ISSUE_REGISTER_PATH
    )

    return (
        cda_registry,
        issue_register,
    )


def run_governance_ai(
    issue_id: str = "DQ-001",
) -> dict:
    """
    Run one governance issue through the
    AI-assisted governance drafting workflow.

    Architecture:

    complete governance evidence
        -> deterministic summary
        -> restricted drafting evidence
        -> LLM business-context drafting
        -> final deterministic validation
        -> human review
    """
    (
        cda_registry,
        issue_register,
    ) = load_governance_artifacts()

    matches = issue_register[
        issue_register[
            "issue_id"
        ] == issue_id
    ]

    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one issue "
            f"with ID '{issue_id}', "
            f"found {len(matches)}."
        )

    issue_row = matches.iloc[0]

    evidence = (
        build_governance_evidence(
            issue_row,
            cda_registry,
        )
    )

    drafting_evidence = (
        build_drafting_evidence(
            evidence
        )
    )

    ai_draft = (
        generate_governance_issue_draft(
            drafting_evidence
        )
    )

    if ai_draft is None:
        return {
            "issue_id": issue_id,
            "accepted": False,
            "validation": {
                "valid": False,
                "errors": [
                    "llm_unavailable_or_invalid_output"
                ],
            },
            "draft": None,
            "evidence": evidence,
            "drafting_evidence": (
                drafting_evidence
            ),
        }

    draft = {
        "summary": (
            build_deterministic_summary(
                evidence
            )
        ),
        "business_context": (
            ai_draft.get(
                "business_context",
                "",
            )
        ),
        "root_cause_status": (
            "UNCONFIRMED"
        ),
        "evidence_used": (
            ai_draft.get(
                "evidence_used",
                [],
            )
        ),
        "requires_human_review": True,
    }

    validation = (
        validate_governance_ai_output(
            draft,
            evidence,
        )
    )

    return {
        "issue_id": issue_id,
        "accepted": validation[
            "valid"
        ],
        "validation": validation,
        "draft": draft,
        "evidence": evidence,
        "drafting_evidence": (
            drafting_evidence
        ),
    }