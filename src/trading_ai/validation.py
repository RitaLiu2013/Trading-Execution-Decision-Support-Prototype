from __future__ import annotations

import pandas as pd


def normalize_categories(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["side_clean"] = out["side"].astype("string").str.strip().str.upper()
    out["asset_class_clean"] = out["asset_class"].astype("string").str.strip()
    out["venue_clean"] = out["venue"].astype("string").str.strip().str.upper()
    return out


def add_quality_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = normalize_categories(df)

    out["flag_duplicate_trade_id"] = out.duplicated(subset="trade_id", keep=False)
    out["flag_missing_arrival_price"] = out["arrival_price"].isna()
    out["flag_missing_vwap_price"] = out["vwap_price"].isna()
    out["flag_invalid_quantity"] = (
        out["order_qty"].le(0)
        | out["executed_qty"].lt(0)
        | out["executed_qty"].gt(out["order_qty"])
    )
    out["flag_invalid_side"] = ~out["side_clean"].isin(["BUY", "SELL"])
    out["flag_nonpositive_price"] = (
        out["avg_execution_price"].le(0)
        | out["arrival_price"].le(0).fillna(False)
        | out["vwap_price"].le(0).fillna(False)
    )
    out["flag_dirty_side"] = out["side"].astype("string") != out["side_clean"]

    # Hard issues prevent the row from being used in arrival-benchmark analysis.
    out["hard_quality_issue"] = (
        out["flag_duplicate_trade_id"]
        | out["flag_missing_arrival_price"]
        | out["flag_invalid_quantity"]
        | out["flag_invalid_side"]
        | out["flag_nonpositive_price"]
    )
    out["analysis_eligible_arrival"] = ~out["hard_quality_issue"]
    out["analysis_eligible_vwap"] = out["analysis_eligible_arrival"] & ~out["flag_missing_vwap_price"]
    return out


def data_quality_summary(df: pd.DataFrame) -> pd.DataFrame:
    flagged = add_quality_flags(df)
    flags = [c for c in flagged.columns if c.startswith("flag_")]
    rows = []
    for col in flags:
        rows.append({"issue": col.removeprefix("flag_"), "row_count": int(flagged[col].sum())})
    rows.extend([
        {"issue": "hard_quality_issue", "row_count": int(flagged["hard_quality_issue"].sum())},
        {"issue": "arrival_analysis_eligible", "row_count": int(flagged["analysis_eligible_arrival"].sum())},
        {"issue": "vwap_analysis_eligible", "row_count": int(flagged["analysis_eligible_vwap"].sum())},
    ])
    return pd.DataFrame(rows)
