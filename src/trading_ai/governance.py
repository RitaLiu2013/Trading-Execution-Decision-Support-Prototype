from __future__ import annotations

import pandas as pd


def run_governance_checks(df: pd.DataFrame) -> pd.DataFrame:
    checks: list[dict] = []

    def add_check(
        field: str,
        rule: str,
        passed_rows: int,
        total_rows: int,
        threshold: float,
    ) -> None:
        pass_rate = passed_rows / total_rows if total_rows else 0.0

        checks.append(
            {
                "field": field,
                "rule": rule,
                "passed_rows": int(passed_rows),
                "total_rows": int(total_rows),
                "pass_rate": round(pass_rate, 4),
                "threshold": threshold,
                "status": "PASS" if pass_rate >= threshold else "FAIL",
            }
        )

    total = len(df)

    valid_trade_id = df["trade_id"].notna()

    add_check(
        "trade_id",
        "Trade ID must be present",
        valid_trade_id.sum(),
        total,
        1.00,
    )

    unique_trade_id = ~df["trade_id"].duplicated(keep=False)

    add_check(
        "trade_id",
        "Trade ID must be unique",
        unique_trade_id.sum(),
        total,
        1.00,
    )

    normalized_side = (
        df["side"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    valid_side = normalized_side.isin(["BUY", "SELL"])

    add_check(
        "side",
        "Side must be BUY or SELL",
        valid_side.sum(),
        total,
        1.00,
    )

    valid_order_qty = (
        df["order_qty"].notna()
        & (df["order_qty"] > 0)
    )

    add_check(
        "order_qty",
        "Order quantity must be positive",
        valid_order_qty.sum(),
        total,
        1.00,
    )

    valid_executed_qty = (
        df["executed_qty"].notna()
        & (df["executed_qty"] >= 0)
        & (df["executed_qty"] <= df["order_qty"])
    )

    add_check(
        "executed_qty",
        "Executed quantity must be between 0 and order quantity",
        valid_executed_qty.sum(),
        total,
        1.00,
    )

    valid_arrival_price = (
        df["arrival_price"].notna()
        & (df["arrival_price"] > 0)
    )

    add_check(
        "arrival_price",
        "Arrival price must be present and positive",
        valid_arrival_price.sum(),
        total,
        0.99,
    )

    valid_vwap_price = (
        df["vwap_price"].notna()
        & (df["vwap_price"] > 0)
    )

    add_check(
        "vwap_price",
        "VWAP price must be present and positive",
        valid_vwap_price.sum(),
        total,
        0.98,
    )

    valid_venue = (
        df["venue"].notna()
        & df["venue"].astype("string").str.strip().ne("")
    )

    add_check(
        "venue",
        "Venue must be present",
        valid_venue.sum(),
        total,
        0.99,
    )

    allowed_asset_classes = {
        "Equity",
        "Fixed Income",
        "FX",
    }

    valid_asset_class = df["asset_class"].isin(
        allowed_asset_classes
    )

    add_check(
        "asset_class",
        "Asset class must belong to the approved list",
        valid_asset_class.sum(),
        total,
        1.00,
    )

    return pd.DataFrame(checks)


ISSUE_METADATA = {
    ("trade_id", "Trade ID must be unique"): {
        "severity": "High",
        "data_owner_role": "Trading Operations",
        "data_steward_role": "Markets Data Steward",
        "issue_type": "Uniqueness",
        "remediation_action": (
            "Investigate duplicate records and determine whether the issue "
            "originates from source data or record-processing logic."
        ),
    },
    (
        "executed_qty",
        "Executed quantity must be between 0 and order quantity",
    ): {
        "severity": "High",
        "data_owner_role": "Trading Operations",
        "data_steward_role": "Markets Data Steward",
        "issue_type": "Validity",
        "remediation_action": (
            "Investigate the affected trade and determine whether the issue "
            "originates from source data or quantity-processing logic."
        ),
    },
}


def build_issue_register(
    quality_report: pd.DataFrame,
) -> pd.DataFrame:
    failed_checks = quality_report[
        quality_report["status"] == "FAIL"
    ].copy()

    issues = []

    for issue_number, (_, row) in enumerate(
        failed_checks.iterrows(),
        start=1,
    ):
        key = (row["field"], row["rule"])

        metadata = ISSUE_METADATA.get(
            key,
            {
                "severity": "Medium",
                "data_owner_role": "To be assigned",
                "data_steward_role": "Markets Data Steward",
                "issue_type": "Data Quality",
                "remediation_action": (
                    "Investigate the failed control and determine root cause."
                ),
            },
        )

        issues.append(
            {
                "issue_id": f"DQ-{issue_number:03d}",
                "field": row["field"],
                "rule": row["rule"],
                "observed_pass_rate": row["pass_rate"],
                "threshold": row["threshold"],
                "severity": metadata["severity"],
                "data_owner_role": metadata["data_owner_role"],
                "data_steward_role": metadata["data_steward_role"],
                "issue_type": metadata["issue_type"],
                "root_cause": "To be investigated",
                "status": "OPEN",
                "remediation_action": metadata["remediation_action"],
                "escalation_required": (
                    "YES"
                    if metadata["severity"] == "High"
                    else "NO"
                ),
            }
        )

    return pd.DataFrame(issues)

# LLM allowed evidence boundary
def build_governance_evidence(
    issue_row: pd.Series,
    cda_registry: pd.DataFrame,
) -> dict:
    """
    Combine one deterministic governance issue with its CDA metadata.

    The returned dictionary is the authoritative evidence package that may
    be supplied to the LLM. The LLM must not change these facts.
    """
    field = str(issue_row["field"])

    matches = cda_registry[
        cda_registry["field_name"] == field
    ]

    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one CDA registry row for field '{field}', "
            f"found {len(matches)}."
        )

    cda = matches.iloc[0]

    return {
        "issue_id": str(issue_row["issue_id"]),
        "field": field,
        "rule": str(issue_row["rule"]),
        "observed_pass_rate": float(issue_row["observed_pass_rate"]),
        "threshold": float(issue_row["threshold"]),
        "severity": str(issue_row["severity"]),
        "status": str(issue_row["status"]),
        "root_cause": str(issue_row["root_cause"]),
        "remediation_action": str(issue_row["remediation_action"]),
        "escalation_required": str(issue_row["escalation_required"]),
        "data_owner_role": str(issue_row["data_owner_role"]),
        "data_steward_role": str(issue_row["data_steward_role"]),
        "business_definition": str(cda["business_definition"]),
        "business_process": str(cda["business_process"]),
        "criticality": str(cda["criticality"]),
        "downstream_use": str(cda["downstream_use"]),
    }