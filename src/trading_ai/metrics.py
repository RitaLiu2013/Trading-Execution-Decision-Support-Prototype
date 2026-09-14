from __future__ import annotations

import numpy as np
import pandas as pd

from .validation import add_quality_flags


def add_execution_metrics(df: pd.DataFrame) -> pd.DataFrame:
    out = add_quality_flags(df)

    out["side_sign"] = np.where(out["side_clean"].eq("BUY"), 1.0, -1.0)
    out.loc[out["flag_invalid_side"], "side_sign"] = np.nan

    out["fill_rate"] = out["executed_qty"] / out["order_qty"]

    out["signed_arrival_slippage_bps"] = (
        out["side_sign"]
        * (out["avg_execution_price"] - out["arrival_price"])
        / out["arrival_price"]
        * 10_000
    )

    out["signed_vwap_slippage_bps"] = (
        out["side_sign"]
        * (out["avg_execution_price"] - out["vwap_price"])
        / out["vwap_price"]
        * 10_000
    )

    out["execution_notional"] = out["executed_qty"] * out["avg_execution_price"]
    out["flag_low_fill"] = out["fill_rate"].lt(0.95)
    out["flag_extreme_arrival_slippage"] = out["signed_arrival_slippage_bps"].abs().gt(250)
    return out
