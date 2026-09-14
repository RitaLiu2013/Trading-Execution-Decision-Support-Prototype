import pandas as pd
from trading_ai.metrics import add_execution_metrics


def test_sign_adjusted_slippage_treats_adverse_buy_and_sell_consistently():
    df = pd.DataFrame({
        "trade_id": ["A", "B"],
        "trade_date": pd.to_datetime(["2026-01-01", "2026-01-01"]),
        "asset_class": ["Equity", "Equity"],
        "side": ["BUY", "SELL"],
        "venue": ["VENUE_A", "VENUE_A"],
        "order_qty": [100, 100],
        "executed_qty": [100, 100],
        "arrival_price": [100.0, 100.0],
        "avg_execution_price": [101.0, 99.0],
        "vwap_price": [100.0, 100.0],
        "spread_bps": [5.0, 5.0],
        "volatility_pct": [1.0, 1.0],
        "participation_rate_pct": [5.0, 5.0],
        "duration_sec": [60, 60],
        "instrument": ["X", "X"],
    })
    out = add_execution_metrics(df)
    assert round(out.loc[0, "signed_arrival_slippage_bps"], 6) == 100.0
    assert round(out.loc[1, "signed_arrival_slippage_bps"], 6) == 100.0
