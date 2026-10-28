# Trading Execution Data Lineage

Synthetic trade records
        ↓
validation.py
        ↓
validated execution dataset
        ↓
metrics.py / analytics.py
        ↓
venue and asset-class analytics
        ↓
outputs and decision-support responses

## Key lineage observations

- `trade_id` originates in the synthetic transaction dataset and is used throughout validation and record-level analysis.
- `side`, `arrival_price` and execution price feed the signed slippage calculation.
- `order_qty` and `executed_qty` feed fill-rate and partial-fill analysis.
- `venue` and `asset_class` feed aggregated execution-quality reporting.
- Validation failures are separated from unusual but valid execution outcomes.