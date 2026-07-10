# Inventory Policies
## Naive Baseline
Use a fixed-quantity periodic reorder policy as a simple non-forecast benchmark. Place the same order quantity every fixed review interval.

## Fixed Reorder-Point Policy
Place a replenishment order when inventory position falls below a fixed reorder point.
Order a fixed replenishment quantity each time the threshold is crossed.
Safety stock is treated as a fixed parameter.

## Order-Up-To Policy
Order enough units to raise inventory position to a fixed target level chosen in advance.
In the current simulator, the effective target is base target plus safety stock.

## Forecast-Driven Order-Up-To Policy
Order enough units to raise inventory position to a target informed by forecasted lead-time demand plus safety stock.
The simulator reads forecast rows from a saved forecast artifact keyed by forecast origin date and target date range.

### Decision Rule
For each simulation date, the policy:
- looks up the saved forecast rows whose `forecast_origin_date` matches the current simulation date
- sums `predicted_demand` from the next day through the configured lead-time window
- sets the order-up-to target to `forecasted_lead_time_demand + safety_stock`
- places an order only if current inventory position is below that target

Inventory position is on-hand inventory plus outstanding orders already in transit.

### Potential Future Refinement
The current MVP policy uses aggregate predicted lead-time demand rather than explicitly projecting inventory day by day through the lead-time window.

A later extension could forecast the within-lead-time inventory trajectory more directly: project expected inventory remaining on the arrival day using current stock, outstanding orders, and predicted daily demand, then place an order to reach the desired arrival-day level. Under the current lost-sales simulator, this may better match how demand timing inside the lead-time window affects stockouts and remaining inventory.

### Supported Forecast Inputs
The current forecast-driven policy is designed to consume any saved forecast artifact that matches the repository forecast CSV contract. In the current project flow, that includes:
- `naive_last_value`
- `moving_average_7`
- `xgboost_recursive_7`

This keeps forecasting and simulation separate. The simulator does not train models or generate predictions during a simulation run. It only reads a saved forecast artifact through `forecast_csv_path`.

Forecast-method details, including how `moving_average_7` and `xgboost_recursive_7` are constructed, are documented in [demand_forecasting.md](/Users/evelynchou/Desktop/School/Personal_Projects/supply_chain/docs/demand_forecasting.md).

### Forecast Artifact Examples
- `{"forecast_driven_order_up_to": {"forecast_name": "naive_last_value", "forecast_csv_path": "data/forecasts/m5_foods_3_080_ca_1/naive_last_value/default/val_forecasts.csv"}}`
- `{"forecast_driven_order_up_to": {"forecast_name": "moving_average_7", "forecast_csv_path": "data/forecasts/m5_foods_3_080_ca_1/moving_average_7/default/val_forecasts.csv"}}`
- `{"forecast_driven_order_up_to": {"forecast_name": "xgboost_recursive_7", "forecast_csv_path": "data/forecasts/m5_foods_3_080_ca_1/xgboost_recursive_7/default/test_forecasts.csv"}}`

## Current Simulator Defaults
- `fixed_quantity_periodic_reorder`: `fixed_order_quantity=40`, `review_interval_days=7`
- `fixed_reorder_point`: `reorder_point=40`, `fixed_order_quantity=80`
- `fixed_target_order_up_to`: `base_target_level=40`, with effective target `base_target_level + safety_stock`
- `forecast_driven_order_up_to`: reads `forecast_name` and `forecast_csv_path` from `--policy-config-json`

## Policy Configuration Surface
Policy-specific overrides are passed through `--policy-config-json` as a JSON object keyed by policy name.

Examples:
- `{"fixed_quantity_periodic_reorder": {"fixed_order_quantity": 40, "review_interval_days": 7}}`
- `{"fixed_reorder_point": {"reorder_point": 50, "fixed_order_quantity": 90}}`
- `{"fixed_target_order_up_to": {"base_target_level": 40}}`
- `{"forecast_driven_order_up_to": {"forecast_name": "moving_average_7", "forecast_csv_path": "data/forecasts/m5_foods_3_080_ca_1/moving_average_7/default/val_forecasts.csv"}}`

## Run-Level Assumptions
These settings are kept separate from policy-specific overrides and apply at the simulator run level:
- Lead time
- Safety stock
- Holding cost
- Stockout penalty
