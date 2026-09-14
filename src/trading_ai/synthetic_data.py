from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from .config import RAW_DATA_PATH


def _base_price(asset_class: str, rng: np.random.Generator) -> float:
    if asset_class == "Equity":
        return float(rng.uniform(20, 250))
    if asset_class == "Fixed Income":
        return float(rng.uniform(80, 120))
    if asset_class == "FX":
        return float(rng.uniform(0.8, 1.5))
    raise ValueError(f"Unsupported asset class: {asset_class}")


def generate_synthetic_trades(
    n: int = 240,
    seed: int = 42,
    output_path: Path | str = RAW_DATA_PATH,
) -> pd.DataFrame:
    """Generate a reproducible synthetic execution dataset.

    The generator deliberately injects data-quality and analytical edge cases.
    It is not intended to reproduce any bank's production data or TCA model.
    """
    rng = np.random.default_rng(seed)

    asset_classes = ["Equity", "Fixed Income", "FX"]
    venues = ["VENUE_A", "VENUE_B", "VENUE_C"]
    sides = ["BUY", "SELL"]

    df = pd.DataFrame({
        "trade_id": [f"TRD{i:04d}" for i in range(1, n + 1)],
        "trade_date": pd.to_datetime(
            rng.choice(pd.date_range("2026-08-01", "2026-08-31"), size=n)
        ),
        "asset_class": rng.choice(asset_classes, size=n, p=[0.45, 0.30, 0.25]),
        "side": rng.choice(sides, size=n),
        "venue": rng.choice(venues, size=n, p=[0.40, 0.35, 0.25]),
        "order_qty": rng.integers(1_000, 50_000, size=n),
        "spread_bps": np.round(rng.lognormal(mean=2.0, sigma=0.45, size=n), 2),
        "volatility_pct": np.round(rng.uniform(0.5, 4.0, size=n), 2),
        "participation_rate_pct": np.round(rng.uniform(1.0, 25.0, size=n), 2),
        "duration_sec": rng.integers(10, 1_800, size=n),
    })

    instrument_map = {
        "Equity": ["EQ_A", "EQ_B", "EQ_C", "EQ_D"],
        "Fixed Income": ["BOND_A", "BOND_B", "BOND_C"],
        "FX": ["EURUSD", "USDJPY", "GBPUSD"],
    }
    df["instrument"] = [rng.choice(instrument_map[ac]) for ac in df["asset_class"]]
    df["arrival_price"] = np.round([_base_price(ac, rng) for ac in df["asset_class"]], 5)

    venue_effect = df["venue"].map({"VENUE_A": 0.0, "VENUE_B": 1.5, "VENUE_C": 3.5}).to_numpy()
    asset_effect = df["asset_class"].map({"Equity": 1.5, "Fixed Income": 2.5, "FX": 0.5}).to_numpy()

    # Known synthetic relationship used to validate the analytics pipeline.
    base_slippage_bps = (
        0.35 * df["spread_bps"].to_numpy()
        + 1.25 * df["volatility_pct"].to_numpy()
        + 0.18 * df["participation_rate_pct"].to_numpy()
        + venue_effect
        + asset_effect
        + rng.normal(0, 4, size=n)
    )

    side_sign = np.where(df["side"].eq("BUY"), 1.0, -1.0)
    df["avg_execution_price"] = np.round(
        df["arrival_price"] * (1 + side_sign * base_slippage_bps / 10_000), 5
    )

    vwap_move_bps = rng.normal(0, 6, size=n)
    df["vwap_price"] = np.round(df["arrival_price"] * (1 + vwap_move_bps / 10_000), 5)

    fill_rates = rng.choice(
        [1.00, 0.98, 0.95, 0.90, 0.80],
        size=n,
        p=[0.72, 0.10, 0.08, 0.06, 0.04],
    )
    df["executed_qty"] = np.round(df["order_qty"] * fill_rates).astype(int)

    # Deliberate tricky cases. These are designed to exercise validation logic.
    df.loc[0, "executed_qty"] = int(df.loc[0, "order_qty"] * 0.35)  # low fill, valid event
    df.loc[1, "arrival_price"] = np.nan  # missing benchmark
    df.loc[2, "executed_qty"] = int(df.loc[2, "order_qty"] + 5_000)  # impossible quantity
    df.loc[3, "trade_id"] = df.loc[4, "trade_id"]  # duplicate ID

    # Extreme adverse execution observation; flag for investigation, do not auto-delete.
    if df.loc[5, "side"] == "BUY":
        df.loc[5, "avg_execution_price"] = round(df.loc[5, "arrival_price"] * 1.09, 5)
    else:
        df.loc[5, "avg_execution_price"] = round(df.loc[5, "arrival_price"] * 0.91, 5)

    df.loc[6, "side"] = " buy "  # dirty categorical value
    df.loc[7, "vwap_price"] = np.nan  # missing secondary benchmark

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df


if __name__ == "__main__":
    frame = generate_synthetic_trades()
    print(f"Generated {len(frame)} rows at {RAW_DATA_PATH}")
