# Experiments

## Current Experiment Scope
The current experiment set includes three SKUs with different demand patterns.

The baseline assumptions are:

- fixed lead time of 5 days
- fixed safety stock of 40 units
- lost sales with no backorders
- holding cost of 0.10 per unit per day
- stockout penalty of 2.00 per unmet unit

The analysis compares:

- three M5 `store x item` series as the main experiment set
- a fixed-quantity periodic reorder naive baseline, a fixed reorder-point policy, an order-up-to policy with a fixed target, and a forecast-driven order-up-to policy
- naive last value, moving average, recursive XGBoost, and Chronos2 forecasting methods for the forecast-driven policy

Policy results are reported under the defined sensitivity analysis settings.

## Sensitivity Analysis
- Fixed lead time: 3, 5, 7 days
- Safety stock: 20, 40, 60 units
- Stockout penalty: 1.00, 2.00, 5.00 per unmet unit
- Holding cost: 0.05, 0.10, 0.20 per unit per day

## Stretch Goals
- Add more advanced forecasting models, especially models that use price and promotion covariates.
- Extend the experiment set beyond the current three SKUs.

## Reported (Simulator/Policy) Metrics 
- Unit fill rate
- Stockout days
- Holding cost
- Stockout penalty
- Total cost
