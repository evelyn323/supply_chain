# Demand Forecasting and Inventory Policy Simulation

## Overview
This project investigates whether more accurate demand forecasts necessarily lead to better inventory decisions.

It combines demand forecasting with an inventory simulator to compare how different replenishment policies affect service levels and inventory cost.

## Key Results
- Built an end-to-end forecasting and inventory simulation pipeline on three M5 retail SKU series with smoother, intermittent, and spikier demand patterns.
- Showed that the best-RMSE forecast model, `xgboost_recursive_7`, did not always produce the best downstream inventory outcome, demonstrating that forecast accuracy alone is not enough to judge operational value.
- Found that forecast-driven replenishment was the lowest-cost policy for the smoother and intermittent SKUs, but a simple fixed target order-up-to policy remained best for the spikier SKU.
- Confirmed the pattern with sensitivity analysis across 9 operating scenarios per SKU by varying lead time, safety stock, holding cost, and stockout penalty.

## Problem Statement
Does better demand forecasting necessarily lead to better inventory decisions?

## Project Overview
The project consists of five main components:
1. **Data Ingestion Pipeline**: Load, validate, clean, and transform real historical demand data.
2. **Inventory Simulator**: Simulate inventory management, replenishment arrivals, fulfilled demand, stockouts, and costs under defined operating assumptions.
3. **Demand Forecasting Models**: Models that forecast expected future demand, used in some replenishment policies for decision making.
4. **Inventory Policy Comparisons**: Compare inventory policies using cost and service metrics.
5. **Sensitivity Analysis**: Test how results change under different lead times, safety-stock levels, and stockout penalties.

## Current Scope
The current project scope simulates a small set of M5 `store x item` series with different demand patterns under a fixed-lead-time, lost-sales inventory simulator with fixed holding cost and stockout penalty assumptions.

The current analysis compares three SKUs with smoother, intermittent, and spikier demand behavior. It evaluates a fixed-quantity periodic reorder naive baseline, a fixed reorder-point policy, an order-up-to policy with a fixed target, and a forecast-driven order-up-to policy using naive last value, moving average, recursive XGBoost, and Chronos2 forecasts.

Sensitivity analysis varies fixed lead time, safety stock, stockout penalty, and holding cost.

Core evaluation metrics include unit fill rate, stockout days, holding cost, stockout penalty, and total cost. Forecast accuracy is evaluated with RMSE.

## Stretch Goals
- Add richer forecasting models, including models that use price and promotion covariates. For example, the zero-shot `Chronos2` forecasting model.
- Extend the analysis beyond the current three-SKU set.

## Out of Scope
- Supplier capacity constraints
- Multi-echelon inventory networks
- Product substitution
- Quantity discounts
- Dynamic pricing
- Real-time production scheduling
- Backorders
- Multi-store optimization

More information about assumptions and extensions is in the detailed documentation files.

## Documentation
- [Data Ingestion Pipeline](docs/data_ingestion_pipeline.md)
- [Inventory Simulator](docs/inventory_simulator.md)
- [Inventory Policies](docs/inventory_policies.md)
- [Demand Forecasting](docs/demand_forecasting.md)
- [Policy Evaluation](docs/policy_evaluation.md)
- [Experiments](docs/experiments.md)
- [Results](docs/results.md)
- [Limitations](docs/limitations.md)

## Repository Structure
- `src/data/`: data loading, validation, and preprocessing
- `src/forecasting/`: forecast baselines and forecasting models
- `src/simulation/`: inventory simulator logic
- `src/policies/`: replenishment policy implementations
- `src/evaluation/`: forecast and policy evaluation utilities
- `tests/`: automated tests
- `data/raw/`: raw downloaded data
- `data/processed/`: cleaned or transformed data artifacts
- `notebooks/eda`: exploratory Jupyter notebooks for dataset inspection and EDA
- `notebooks/simulation`: exploratory Jupyter notebooks for simulator-output inspection and plotting

## Setup and Usage
### Environment Setup
The project uses a Conda environment defined in [environment.yml](environment.yml).

```bash
conda env create -f environment.yml
conda activate supply-chain
```

### Data Preparation
Generate the processed daily dataset for one SKU:

```bash
python -m src.data.build_processed --item-id FOODS_3_080 --store-id CA_1
```

This saves the processed daily series to `data/processed/m5_foods_3_080_ca_1_daily.csv` by default.

Generate chronological train, validation, and test splits from a processed SKU series:

```bash
python -m src.data.build_splits --item-id FOODS_3_080 --store-id CA_1
```

By default, the split fractions come from `prepare_splits`. You can optionally override either held-out fraction from the CLI:

```bash
python -m src.data.build_splits --item-id FOODS_3_080 --store-id CA_1 --val-frac 0.2 --test-frac 0.1
```

This saves `train.csv`, `validation.csv`, and `test.csv` under `data/splits/m5_foods_3_080_ca_1/` by default.

### Forecasting
Forecasting artifacts are built and saved separately from simulation runs. The simulator reads saved forecast CSVs for forecast-driven policies rather than training or generating forecasts live.

#### Build Forecast Artifacts
Build and save naive-last-value forecast artifacts for one split:

```bash
python -m src.forecasting.build_forecasts --item-id FOODS_3_080 --store-id CA_1 --split val --forecast naive_last_value
```

This saves forecast rows under `data/forecasts/m5_foods_3_080_ca_1/naive_last_value/default/val_forecasts.csv` by default. Each row stores a forecast origin date, target date, horizon day, and predicted demand so forecast-driven policies can read the saved artifact later.

Build and save a moving-average forecast artifact with a 7-day window:

```bash
python -m src.forecasting.build_forecasts --item-id FOODS_3_080 --store-id CA_1 --split val --forecast moving_average --context-window-days 7
```

This saves forecast rows under `data/forecasts/m5_foods_3_080_ca_1/moving_average_7/default/val_forecasts.csv` by default.

Train and save a recursive XGBoost model with a 7-day rolling feature window:

```bash
python -m src.forecasting.train_xgboost --item-id FOODS_3_080 --store-id CA_1 --context-window-days 7
```

This saves the model under `data/models/m5_foods_3_080_ca_1/xgboost_recursive_7/default/model.json` by default and uses the validation split for early stopping when enough validation rows are available.

Build and save recursive XGBoost forecast artifacts for one split from the saved model:

```bash
python -m src.forecasting.build_forecasts --item-id FOODS_3_080 --store-id CA_1 --split test --forecast xgboost_recursive --context-window-days 7
```

This saves forecast rows under `data/forecasts/m5_foods_3_080_ca_1/xgboost_recursive_7/default/test_forecasts.csv` by default. The saved model is reused, while the forecast CSV still stores one predicted demand row per forecast origin date and horizon day.

More detail on the forecast artifact contract and forecast-to-policy boundary is in [docs/demand_forecasting.md](docs/demand_forecasting.md).

Build and save a Chronos2 forecast artifact with a 7-day context window:

```bash
python -m src.forecasting.build_forecasts --item-id FOODS_3_080 --store-id CA_1 --split val --forecast chronos2 --context-window-days 7
```

This saves forecast rows under `data/forecasts/m5_foods_3_080_ca_1/chronos2/default/val_forecasts.csv` by default.

Build and save recursive XGBoost forecast artifacts for the validation split from the saved model:

```bash
python -m src.forecasting.build_forecasts --item-id FOODS_3_080 --store-id CA_1 --split val --forecast xgboost_recursive --context-window-days 7
```

This saves forecast rows under `data/forecasts/m5_foods_3_080_ca_1/xgboost_recursive_7/default/val_forecasts.csv` by default.

#### Evaluate Forecast Artifacts
Evaluate one saved forecast CSV with RMSE:

```bash
python -m src.forecasting.evaluate_forecasts --item-id FOODS_3_080 --store-id CA_1 --split val --forecast-name moving_average_7
```

This reads `data/forecasts/.../<forecast_name>/default/val_forecasts.csv`, joins forecast `target_date` rows to the realized demand in the requested split, and prints split-level RMSE.

### Experiments
The experiment runner expects all forecast artifacts to be built ahead of time. It evaluates the saved forecast CSVs, runs the full sensitivity sweep across all policies, and writes reproducible analysis outputs under `data/analysis/`.

Run the full analysis after building the required forecast artifacts:

```bash
python -m src.experiments.run_mvp_analysis
```

### Simulation
#### Run the Simulator
Run the simulator for one saved split:

```bash
python -m src.simulation.run_simulation --item-id FOODS_3_080 --store-id CA_1 --split val
```

By default, the simulator reads split CSVs from `data/splits`, writes daily snapshots to `data/simulation`, uses the previous-day-demand-plus-safety-stock initial state, runs the fixed-quantity periodic reorder policy, and applies the default simulator assumptions.

Supported policies:
- `fixed_quantity_periodic_reorder`: orders a fixed quantity on a fixed review interval
- `fixed_reorder_point`: orders a fixed quantity when inventory position falls below a reorder point
- `fixed_target_order_up_to`: orders up to `base_target_level + safety_stock`
- `forecast_driven_order_up_to`: orders up to forecasted lead-time demand plus safety stock using a saved forecast artifact

Default policy settings and parameter details are summarized in [docs/inventory_policies.md](docs/inventory_policies.md).

You can optionally override the split location, output location, selected split, simulator components, and operating assumptions from the CLI:

```bash
python -m src.simulation.run_simulation \
  --item-id FOODS_3_080 \
  --store-id CA_1 \
  --split test \
  --split-dir data/splits \
  --output-dir data/simulation \
  --initial-state dummy \
  --policy fixed_quantity_periodic_reorder \
  --policy-config-json '{"fixed_quantity_periodic_reorder": {"fixed_order_quantity": 40, "review_interval_days": 7}}' \
  --lead-time-days 5 \
  --safety-stock 40 \
  --holding-cost 0.10 \
  --stockout-penalty 2.00
```

This saves daily simulation snapshots under `data/simulation/m5_foods_3_080_ca_1/<policy>/<assumption_profile>/` by default. The default assumption profile is `default`, for example `data/simulation/m5_foods_3_080_ca_1/fixed_quantity_periodic_reorder/default/val_daily_snapshots.csv`. If you change simulator assumptions for sensitivity analysis, the path uses a deterministic slug such as `lt_3_ss_40_hc_0.1_sp_2`. If you use non-default policy overrides, the simulator adds one policy-config folder before the assumption profile, for example `data/simulation/m5_foods_3_080_ca_1/fixed_target_order_up_to/base-target-level_80/default/val_daily_snapshots.csv`.

#### Forecast-Driven Example
Example forecast-driven simulator run:

```bash
python -m src.simulation.run_simulation \
  --item-id FOODS_3_080 \
  --store-id CA_1 \
  --split val \
  --policy forecast_driven_order_up_to \
  --policy-config-json '{"forecast_driven_order_up_to": {"forecast_name": "moving_average_7", "forecast_csv_path": "data/forecasts/m5_foods_3_080_ca_1/moving_average_7/default/val_forecasts.csv", "context_window_days": 7}}'
```

#### Policy Config Examples
Policy config examples:
- `{"fixed_quantity_periodic_reorder": {"fixed_order_quantity": 40, "review_interval_days": 7}}`
- `{"fixed_reorder_point": {"reorder_point": 50, "fixed_order_quantity": 90}}`
- `{"fixed_target_order_up_to": {"base_target_level": 40}}`
- `{"forecast_driven_order_up_to": {"forecast_name": "moving_average_7", "forecast_csv_path": "data/forecasts/m5_foods_3_080_ca_1/moving_average_7/default/val_forecasts.csv", "context_window_days": 7}}`

#### Simulator Flags
Valid simulator flag values:
- `--split`: `train`, `val`, or `test`
- `--split-dir`: path to the directory containing saved split folders
- `--output-dir`: path to the directory where daily simulation snapshots should be written
- `--initial-state`: `dummy` or `prev_day_demand_plus_safety_stock`
- `--policy`: `dummy`, `fixed_quantity_periodic_reorder`, `fixed_reorder_point`, `fixed_target_order_up_to`, or `forecast_driven_order_up_to`
- `--policy-config-json`: optional JSON object keyed by policy name
- `--lead-time-days`: integer
- `--safety-stock`: numeric value
- `--holding-cost`: numeric value
- `--stockout-penalty`: numeric value
