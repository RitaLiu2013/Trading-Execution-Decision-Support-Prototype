from trading_ai.analytics import load_trades


def test_known_quality_traps_are_detected():
    df = load_trades()
    assert df["flag_duplicate_trade_id"].sum() >= 2
    assert df["flag_missing_arrival_price"].sum() >= 1
    assert df["flag_missing_vwap_price"].sum() >= 1
    assert df["flag_invalid_quantity"].sum() >= 1
    assert df["flag_dirty_side"].sum() >= 1
    assert df["flag_extreme_arrival_slippage"].sum() >= 1


def test_low_fill_is_not_automatically_a_hard_quality_error():
    df = load_trades()
    low_fill = df[df["flag_low_fill"]]
    assert not low_fill.empty
    assert (~low_fill["hard_quality_issue"]).any()
