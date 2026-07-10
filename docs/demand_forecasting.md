# Demand Forecasting

## Scope
Start with demand-history-only forecasting methods. The current forecasting layer is intentionally narrow: produce saved forecast artifacts that can later be consumed by the simulator.

The simulator does not train models or generate predictions live during a simulation run. Forecasting stays separate from simulation through saved CSV artifacts.

## Forecast Artifact Contract
The current artifact contract is one CSV per SKU, forecast method, config, and split.

Each row stores:
- `forecast_origin_date`
- `target_date`
- `horizon_day`
- `predicted_demand`

The simulator later reads these saved rows for the chosen policy and sums the relevant future dates over the lead-time window.

## Current Forecast Methods

### Naive Last Value
For each forecast origin date, predict that every future horizon day will equal the most recently observed demand value available at that origin date.

This is a simple persistence baseline:
- input: prior observed demand history
- one-step logic: `prediction = last observed demand`
- multi-step behavior: the same predicted value is repeated across all saved horizon days for that origin date

### Moving Average
For each forecast origin date, predict that every future horizon day will equal the mean demand over the trailing `context_window_days`.

In the current MVP flow, the main moving-average variant is `moving_average_7`.

This method uses:
- input: prior observed demand history
- feature: trailing mean over the last `context_window_days`
- multi-step behavior: the same moving-average value is repeated across all saved horizon days for that origin date

### Recursive XGBoost
The current learned model is a recursive one-step XGBoost regressor. It predicts one next-day demand value at a time, then feeds each prediction back into the history to predict subsequent horizon days.

In the current MVP flow, the main XGBoost variant is `xgboost_recursive_7`.

The current feature set includes:
- lagged demand at 1, 7, 14, and 28 days
- rolling mean demand over the trailing `context_window_days`
- calendar features: `day_of_week`, `month`, and `year`

The current implementation does not use price, promotions, SNAP flags, or other external covariates.

For `--context-window-days 7`, the model uses a 7-day rolling mean feature, but it is not limited to only the last 7 raw daily values. It also uses the fixed lag features above.

### Training and Validation
The XGBoost model is trained on the training split and uses the validation split for early stopping when enough validation rows are available.

The current setup is intentionally simple:
- objective: squared error regression
- `n_estimators=200`
- `max_depth=4`
- `learning_rate=0.05`
- `subsample=0.8`
- `colsample_bytree=0.8`

This is meant to provide a stronger learned benchmark without turning the project into a full forecasting-model tuning exercise.

## Forecast Horizon Behavior
All current forecast builders save multi-step forecast rows for each forecast origin date.

The multi-step behavior differs by method:
- `naive_last_value`: repeats the last observed demand across all horizons
- `moving_average_*`: repeats the trailing moving average across all horizons
- `xgboost_recursive_*`: predicts one step at a time recursively, using earlier predictions to form later-horizon features

## Forecasting Metrics
Use RMSE as the main forecast accuracy metric.

Forecast bias can be added later as an extension if systematic over- or under-forecasting becomes important to the analysis.

## Forecast-to-Policy Boundary
Forecasts determine expected future demand, but the simulator remains responsible for converting those saved predictions into replenishment decisions.

The forecast-driven inventory policy reads a saved forecast artifact, selects the rows matching the current simulation date, and aggregates the relevant target dates over the lead-time window. Policy behavior is documented in [inventory_policies.md](/Users/evelynchou/Desktop/School/Personal_Projects/supply_chain/docs/inventory_policies.md).
