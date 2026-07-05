# Demand Forecasting
## Forecasting Baselines
Start with demand-history-only baselines. More complex models may optionally incorporate promotions and prices as covariates.
Save forecast outputs as standalone artifacts rather than generating live predictions inside the simulator.
The current artifact contract is one CSV per SKU, forecast method, config, and split.
Each row stores `forecast_origin_date`, `target_date`, `horizon_day`, and `predicted_demand`.
## Feature Engineering
## Forecasting Metrics
Use RMSE as the main forecast accuracy metric.

Optionally consider forecast bias as an extension for evaluating systematic over- or under-forecasting.
## Forecast-to-Policy Integration 
Forecasts determine expected demand over the lead-time period. This then determines the order-up-to target or replenishment quantity.
The simulator reads the saved forecast artifact for the chosen policy rather than training or inferring forecasts live during the simulation run.
