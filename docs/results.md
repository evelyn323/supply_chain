# Results

## Summary
This project tested whether forecast-driven replenishment outperforms simpler non-forecast inventory policies across different demand patterns.

The main result is a demand-pattern-specific threshold story:

- some SKUs are easy enough that even weak forecasts improve replenishment decisions
- some SKUs benefit more as forecast accuracy improves
- spikier SKUs may require much stronger forecasts, or a different policy design, before forecast-driven replenishment reliably beats simple policies

## Setup
Three M5 SKUs were selected to represent different demand patterns:

- `FOODS_3_080 / CA_1`: smoother demand
- `FOODS_3_234 / WI_2`: more intermittent demand
- `HOUSEHOLD_1_474 / TX_2`: spikier demand

In practical terms:

- `FOODS_3_080 / CA_1` has steadier day-to-day demand with relatively few zero-sales days
- `FOODS_3_234 / WI_2` has more low-demand or zero-demand periods, but is still comparatively flat outside those gaps
- `HOUSEHOLD_1_474 / TX_2` shows larger upward demand spikes, making missed peaks more operationally costly

Forecast methods:

- `naive_last_value`
- `moving_average_7`
- `xgboost_recursive_7`
- `chronos2`

Inventory policies:

- `fixed_quantity_periodic_reorder`
- `fixed_reorder_point`
- `fixed_target_order_up_to`
- `forecast_driven_order_up_to`

Outputs:

- [forecast_rmse_table.csv](../data/analysis/three_sku_docs/val/forecast_rmse_table.csv)
- [final_simulation_table.csv](../data/analysis/three_sku_docs/val/final_simulation_table.csv)

## Forecast Accuracy
`xgboost_recursive_7` had the best RMSE on all three SKUs.

| SKU | Best RMSE model | RMSE |
| --- | --- | ---: |
| `FOODS_3_080 / CA_1` | `xgboost_recursive_7` | 5.6758 |
| `FOODS_3_234 / WI_2` | `xgboost_recursive_7` | 36.1354 |
| `HOUSEHOLD_1_474 / TX_2` | `xgboost_recursive_7` | 9.2211 |

RMSE alone was not enough to explain inventory performance.

## Baseline Inventory Results
Baseline assumptions:

- lead time = 5
- safety stock = 40
- holding cost = 0.10
- stockout penalty = 2.00

| SKU | Best result | Total cost | Fill rate | Interpretation |
| --- | --- | ---: | ---: | --- |
| `FOODS_3_080 / CA_1` | forecast-driven with `xgboost_recursive_7` | 1340.7 | 0.9796 | Forecast-driven replenishment clearly outperformed simple policies |
| `FOODS_3_234 / WI_2` | forecast-driven with `xgboost_recursive_7` | 8583.3 | 0.7199 | Forecast-driven replenishment still outperformed simple policies |
| `HOUSEHOLD_1_474 / TX_2` | `fixed_target_order_up_to` | 2682.8 | 0.8248 | Simple non-forecast replenishment remained best |

Compared with the best non-forecast baseline:

- `FOODS_3_080 / CA_1`: best forecast-driven policy reduced total cost by about `2390`
- `FOODS_3_234 / WI_2`: best forecast-driven policy reduced total cost by about `5556`
- `HOUSEHOLD_1_474 / TX_2`: best forecast-driven policy was still about `519` worse

## Demand-Pattern Interpretation
### Smoother SKU: `FOODS_3_080 / CA_1`
This SKU was easy enough that forecast-driven replenishment consistently helped. Better forecasts improved the result further, but even weaker forecast-driven variants outperformed the non-forecast policies. This is the clearest low-threshold case.

### Intermittent SKU: `FOODS_3_234 / WI_2`
This SKU was harder than the smoother food item, but still forecastable enough that forecast-driven replenishment beat the non-forecast policies. The results suggest that intermittent demand is not automatically a case where simple policies win. If the series is flat enough outside low-demand periods, even weaker forecasts can still be useful.

### Spiky SKU: `HOUSEHOLD_1_474 / TX_2`
This SKU tells the opposite story. Even though `xgboost_recursive_7` had the best RMSE, forecast-driven replenishment did not beat the best simple policy on total cost. This is consistent with a higher threshold: the current forecasts were not strong enough, or not accurate in the right way around spikes, for forecast-driven replenishment to pay off.

## Sensitivity Analysis
The sensitivity analysis acts as a sanity check on that threshold interpretation.

Across 9 tested scenarios for each SKU:

- `FOODS_3_080 / CA_1`: forecast-driven was best in `9/9`
- `FOODS_3_234 / WI_2`: forecast-driven was best in `9/9`
- `HOUSEHOLD_1_474 / TX_2`: non-forecast policies were best in `8/9`

So the baseline pattern held under changes to lead time, safety stock, holding cost, and stockout penalty:

- smoother and flatter-demand SKUs benefited robustly from forecast-driven replenishment
- the spikier SKU usually did not

## Conclusion
The results support a demand-pattern-specific threshold view of forecast value in replenishment.

- some SKUs are easy enough that even weak forecasts help
- some SKUs reward incremental improvements in forecast accuracy
- spiky SKUs may require much stronger forecasts, or a different replenishment policy, before forecast-driven methods outperform simple fixed rules

The practical takeaway is that forecast quality should be evaluated together with downstream inventory performance, and the threshold for “good enough” forecast accuracy depends on the SKU’s demand pattern.
