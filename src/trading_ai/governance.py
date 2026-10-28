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

    # 1. Trade ID completeness
    valid_trade_id = df["trade_id"].notna()

    add_check(
        "trade_id",
        "Trade ID must be present",
        valid_trade_id.sum(),
        total,
        1.00,
    )

    # 2. Trade ID uniqueness
    unique_trade_id = ~df["trade_id"].duplicated(keep=False)

    add_check(
        "trade_id",
        "Trade ID must be unique",
        unique_trade_id.sum(),
        total,
        1.00,
    )

    # 3. Trade side validity
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

    # 4. Order quantity validity
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

    # 5. Executed quantity validity
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

    # 6. Arrival-price completeness and validity
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

    # 7. VWAP-price completeness and validity
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

    # 8. Venue validity
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

    # 9. Asset-class validity
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