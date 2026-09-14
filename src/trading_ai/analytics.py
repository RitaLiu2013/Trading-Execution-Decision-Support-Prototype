from __future__ import annotations

from pathlib import Path
import pandas as pd

from .config import RAW_DATA_PATH
from .metrics import add_execution_metrics
from .validation import data_quality_summary


def load_trades(path: Path | str = RAW_DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["trade_date"])
    return add_execution_metrics(df)


def _arrival_universe(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[df["analysis_eligible_arrival"]].copy()


def get_worst_executions(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    cols = [
        "trade_id", "trade_date", "asset_class_clean", "instrument", "side_clean",
        "venue_clean", "order_qty", "executed_qty", "fill_rate", "spread_bps",
        "volatility_pct", "participation_rate_pct", "signed_arrival_slippage_bps",
        "flag_extreme_arrival_slippage",
    ]
    return (
        _arrival_universe(df)
        .sort_values("signed_arrival_slippage_bps", ascending=False)
        .head(n)[cols]
        .reset_index(drop=True)
    )


def summarize_by_venue(df: pd.DataFrame) -> pd.DataFrame:
    x = _arrival_universe(df)
    grouped = x.groupby("venue_clean", observed=True)
    summary = grouped.agg(
        trades=("trade_id", "count"),
        avg_slippage_bps=("signed_arrival_slippage_bps", "mean"),
        median_slippage_bps=("signed_arrival_slippage_bps", "median"),
        p90_slippage_bps=("signed_arrival_slippage_bps", lambda s: s.quantile(0.90)),
        avg_fill_rate=("fill_rate", "mean"),
        partial_fill_rate=("flag_low_fill", "mean"),
        avg_spread_bps=("spread_bps", "mean"),
    ).reset_index()
    return summary.sort_values("avg_slippage_bps", ascending=False).reset_index(drop=True)


def summarize_by_asset_class(df: pd.DataFrame) -> pd.DataFrame:
    x = _arrival_universe(df)
    grouped = x.groupby("asset_class_clean", observed=True)
    summary = grouped.agg(
        trades=("trade_id", "count"),
        avg_slippage_bps=("signed_arrival_slippage_bps", "mean"),
        median_slippage_bps=("signed_arrival_slippage_bps", "median"),
        p90_slippage_bps=("signed_arrival_slippage_bps", lambda s: s.quantile(0.90)),
        avg_fill_rate=("fill_rate", "mean"),
        avg_spread_bps=("spread_bps", "mean"),
        avg_volatility_pct=("volatility_pct", "mean"),
    ).reset_index()
    return summary.sort_values("avg_slippage_bps", ascending=False).reset_index(drop=True)


def find_partial_fills(df: pd.DataFrame, threshold: float = 0.95, n: int = 20) -> pd.DataFrame:
    cols = [
        "trade_id", "asset_class_clean", "instrument", "side_clean", "venue_clean",
        "order_qty", "executed_qty", "fill_rate", "signed_arrival_slippage_bps",
    ]
    return (
        df.loc[df["fill_rate"].lt(threshold)]
        .sort_values("fill_rate", ascending=True)
        .head(n)[cols]
        .reset_index(drop=True)
    )


def get_data_quality_summary(df: pd.DataFrame) -> pd.DataFrame:
    raw_cols = [
        "trade_id", "trade_date", "asset_class", "side", "venue", "order_qty",
        "executed_qty", "arrival_price", "avg_execution_price", "vwap_price",
        "spread_bps", "volatility_pct", "participation_rate_pct", "duration_sec",
        "instrument",
    ]
    raw = df[[c for c in raw_cols if c in df.columns]].copy()
    return data_quality_summary(raw)


def lookup_trade(df: pd.DataFrame, trade_id: str) -> pd.DataFrame:
    return df.loc[df["trade_id"].eq(trade_id)].copy().reset_index(drop=True)
