# Experiments

## MVP
- Simulate a single SKU.
- Assume fixed lead time of 5 days and fixed safety stock of 40 units.
- Model stockouts as lost sales with no backorders.
- Use a holding cost of 0.10 per unit per day and a stockout penalty of 2.00 per unmet unit.
- Use one M5 `store x item` series as the main experiment.
- Compare a fixed-quantity periodic reorder naive baseline, a fixed reorder-point policy, an order-up-to policy with a fixed target, and a forecast-driven order-up-to policy.
- Use naive last value and moving average forecasting methods for the forecast-driven policy.
- Report policy results under the defined sensitivity analysis settings.

## Sensitivity Analysis
- Fixed lead time: 3, 5, 7 days
- Safety stock: 20, 40, 60 units
- Stockout penalty: 1.00, 2.00, 5.00 per unmet unit
- Holding cost: 0.05, 0.10, 0.20 per unit per day

## Stretch Goals
- Add more advanced forecasting models, especially models that use price and promotion covariates. For example the zero-shot `Chronos2`.
- Add 2-3 SKUs, including the stretch SKUs already identified in the data documentation.

## Reported (Simulator/Policy) Metrics 
- Unit fill rate
- Stockout days
- Holding cost
- Stockout penalty
- Total cost
