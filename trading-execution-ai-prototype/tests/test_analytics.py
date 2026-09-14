from trading_ai.analytics import get_worst_executions, load_trades, summarize_by_venue


def test_worst_execution_contains_injected_extreme_case():
    df = load_trades()
    worst = get_worst_executions(df, n=5)
    assert worst["signed_arrival_slippage_bps"].max() > 800


def test_venue_summary_has_expected_columns():
    df = load_trades()
    summary = summarize_by_venue(df)
    expected = {"venue_clean", "trades", "avg_slippage_bps", "median_slippage_bps", "p90_slippage_bps", "avg_fill_rate"}
    assert expected.issubset(summary.columns)
