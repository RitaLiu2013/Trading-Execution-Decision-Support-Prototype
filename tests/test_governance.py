from pathlib import Path

import pandas as pd

from trading_ai.governance import run_governance_checks


def _get_check(
    report: pd.DataFrame,
    field: str,
    rule: str,
) -> pd.Series:
    result = report[
        (report["field"] == field)
        & (report["rule"] == rule)
    ]

    assert len(result) == 1

    return result.iloc[0]


def _valid_test_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trade_id": ["T1", "T2", "T3"],
            "side": ["BUY", "SELL", "BUY"],
            "order_qty": [100, 200, 150],
            "executed_qty": [100, 150, 75],
            "arrival_price": [100.0, 101.0, 99.0],
            "vwap_price": [100.1, 100.9, 99.2],
            "venue": ["VENUE_A", "VENUE_B", "VENUE_A"],
            "asset_class": [
                "Equity",
                "Fixed Income",
                "FX",
            ],
        }
    )


def test_valid_dataset_passes_all_governance_checks():
    df = _valid_test_dataframe()

    report = run_governance_checks(df)

    assert len(report) == 9
    assert (report["status"] == "PASS").all()


def test_duplicate_trade_id_fails_uniqueness_control():
    df = _valid_test_dataframe()

    df.loc[1, "trade_id"] = "T1"

    report = run_governance_checks(df)

    check = _get_check(
        report,
        "trade_id",
        "Trade ID must be unique",
    )

    assert check["status"] == "FAIL"
    assert check["passed_rows"] == 1
    assert check["total_rows"] == 3


def test_executed_quantity_above_order_quantity_fails():
    df = _valid_test_dataframe()

    df.loc[0, "executed_qty"] = 150
    df.loc[0, "order_qty"] = 100

    report = run_governance_checks(df)

    check = _get_check(
        report,
        "executed_qty",
        "Executed quantity must be between 0 and order quantity",
    )

    assert check["status"] == "FAIL"
    assert check["passed_rows"] == 2


def test_side_normalisation_accepts_whitespace_and_lowercase():
    df = _valid_test_dataframe()

    df.loc[0, "side"] = " buy "
    df.loc[1, "side"] = "sell"

    report = run_governance_checks(df)

    check = _get_check(
        report,
        "side",
        "Side must be BUY or SELL",
    )

    assert check["status"] == "PASS"


def test_project_dataset_produces_expected_governance_results():
    project_root = Path(__file__).resolve().parents[1]
    data_path = project_root / "data" / "synthetic_trades.csv"

    df = pd.read_csv(data_path)

    report = run_governance_checks(df)

    trade_uniqueness = _get_check(
        report,
        "trade_id",
        "Trade ID must be unique",
    )

    executed_quantity = _get_check(
        report,
        "executed_qty",
        "Executed quantity must be between 0 and order quantity",
    )

    arrival_price = _get_check(
        report,
        "arrival_price",
        "Arrival price must be present and positive",
    )

    vwap_price = _get_check(
        report,
        "vwap_price",
        "VWAP price must be present and positive",
    )

    assert trade_uniqueness["status"] == "FAIL"
    assert trade_uniqueness["passed_rows"] == 238

    assert executed_quantity["status"] == "FAIL"
    assert executed_quantity["passed_rows"] == 239

    assert arrival_price["status"] == "PASS"
    assert arrival_price["passed_rows"] == 239

    assert vwap_price["status"] == "PASS"
    assert vwap_price["passed_rows"] == 239