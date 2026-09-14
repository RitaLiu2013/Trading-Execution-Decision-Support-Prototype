# Evaluation report
This report is generated from the deterministic parts of the prototype. RAG/LLM evaluation is intentionally kept separate because it depends on the local embedding model and Ollama runtime.
## Fast evaluation summary
- Router cases passed: **11/11**
- Data-quality checks passed: **7/7**
- Raw rows: **240**
- Arrival-analysis eligible rows: **236**
- Hard-quality-issue rows: **4**
- Extreme arrival-slippage flags: **1**

## Injected edge cases detected
- `duplicate_trade_id`: 2 rows
- `missing_arrival_price`: 1 rows
- `missing_vwap_price`: 1 rows
- `invalid_quantity`: 1 rows
- `invalid_side`: 0 rows
- `nonpositive_price`: 0 rows
- `dirty_side`: 1 rows
- `hard_quality_issue`: 4 rows
- `arrival_analysis_eligible`: 236 rows
- `vwap_analysis_eligible`: 235 rows

## Router evaluation

| question                                              | expected    | actual      | pass   |
|:------------------------------------------------------|:------------|:------------|:-------|
| What is implementation shortfall?                     | knowledge   | knowledge   | True   |
| Why can liquidity affect execution quality?           | knowledge   | knowledge   | True   |
| What does VWAP mean?                                  | knowledge   | knowledge   | True   |
| Which venue has the worst average execution slippage? | data        | data        | True   |
| Show the top 5 worst executions                       | data        | data        | True   |
| Show partial fills                                    | data        | data        | True   |
| What data quality issues are present?                 | data        | data        | True   |
| Compare execution by asset class                      | data        | data        | True   |
| Show TRD0010                                          | data        | data        | True   |
| How do I make pizza?                                  | unsupported | unsupported | True   |
| What problem does MCP solve?                          | unsupported | unsupported | True   |

## Data-quality evaluation

| check                            | pass   |
|:---------------------------------|:-------|
| duplicate_trade_id_rows_detected | True   |
| missing_arrival_detected         | True   |
| missing_vwap_detected            | True   |
| invalid_quantity_detected        | True   |
| dirty_side_detected              | True   |
| extreme_slippage_detected        | True   |
| low_fill_detected                | True   |

## Venue summary

| venue_clean   |   trades |   avg_slippage_bps |   median_slippage_bps |   p90_slippage_bps |   avg_fill_rate |   partial_fill_rate |   avg_spread_bps |
|:--------------|---------:|-------------------:|----------------------:|-------------------:|----------------:|--------------------:|-----------------:|
| VENUE_B       |       85 |            21.0659 |               10.7102 |            16.5010 |          0.9719 |              0.1882 |           7.4340 |
| VENUE_C       |       65 |            12.8770 |               13.4220 |            16.6778 |          0.9802 |              0.1385 |           7.9405 |
| VENUE_A       |       86 |             9.8022 |                9.8034 |            15.7762 |          0.9827 |              0.1163 |           8.6394 |

## Notes on interpretation

- The synthetic generator intentionally creates known relationships between spread, volatility, participation rate, venue/asset-class effects and slippage. These are **not empirical market findings**.
- Mean and median are shown together because the deliberately injected extreme execution can distort the mean.
- The outlier is flagged for investigation rather than automatically deleted.
