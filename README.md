# Demand Forecasting and Inventory Policy Simulation

## Overview
This project investigates whether more accurate demand forecasts necessarily lead to better inventory decisions.

It combines demand forecasting with an inventory simulator to compare how different replenishment policies affect service levels and inventory cost.

## Problem Statement
Does better demand forecasting necessarily lead to better inventory decisions?

## Project Overview
The project consists of five main components:
1. **Data Ingestion Pipeline**: Load, validate, clean, and transform real historical demand data.
2. **Inventory Simulator**: Simulate inventory management, replenishment arrivals, fulfilled demand, stockouts, and costs under defined operating assumptions.
3. **Demand Forecasting Models**: Models that forecast expected future demand, used in some replenishment policies for decision making.
4. **Inventory Policy Comparisons**: Compare inventory policies using cost and service metrics.
5. **Sensitivity Analysis**: Test how results change under different lead times, safety-stock levels, and stockout penalties.

## MVP Scope
The minimum strong version of the project simulates one M5 `store x item` series under a fixed-lead-time, lost-sales inventory simulator with fixed holding cost and stockout penalty assumptions.

The MVP compares a fixed-quantity periodic reorder naive baseline, a fixed reorder-point policy, an order-up-to policy with a fixed target, and a forecast-driven order-up-to policy using at least naive last value and moving average forecasts.

Sensitivity analysis varies fixed lead time, safety stock, stockout penalty, and holding cost.

Core evaluation metrics include unit fill rate, stockout days, holding cost, stockout penalty, and total cost. Forecast accuracy is evaluated with RMSE.

## Stretch Goals
- Add richer forecasting models, including models that use price and promotion covariates. For example, the zero-shot `Chronos2` forecasting model.
- Extend the analysis to 2-3 additional SKUs with different demand patterns.

## Out of Scope
- Supplier capacity constraints
- Multi-echelon inventory networks
- Product substitution
- Quantity discounts
- Dynamic pricing
- Real-time production scheduling
- Backorders
- Multi-store optimization

More informtion about assumptions and extensions are in the detailed documentation files.

## Documentation
- [Data Ingestion Pipeline](/Users/evelynchou/Desktop/School/Personal_Projects/supply_chain/docs/data_ingestion_pipeline.md)
- [Inventory Simulator](/Users/evelynchou/Desktop/School/Personal_Projects/supply_chain/docs/inventory_simulator.md)
- [Inventory Policies](/Users/evelynchou/Desktop/School/Personal_Projects/supply_chain/docs/inventory_policies.md)
- [Demand Forecasting](/Users/evelynchou/Desktop/School/Personal_Projects/supply_chain/docs/demand_forecasting.md)
- [Policy Evaluation](/Users/evelynchou/Desktop/School/Personal_Projects/supply_chain/docs/policy_evaluation.md)
- [Experiments](/Users/evelynchou/Desktop/School/Personal_Projects/supply_chain/docs/experiments.md)
- [Results](/Users/evelynchou/Desktop/School/Personal_Projects/supply_chain/docs/results.md)
- [Limitations](/Users/evelynchou/Desktop/School/Personal_Projects/supply_chain/docs/limitations.md)

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
The project uses a Conda environment defined in [environment.yml](/Users/evelynchou/Desktop/School/Personal_Projects/supply_chain/environment.yml).

```bash
conda env create -f environment.yml
conda activate supply-chain
```

Generate the processed daily dataset for the MVP SKU:

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

Run the simulator for one saved split:

```bash
python -m src.simulation.run_simulation --item-id FOODS_3_080 --store-id CA_1 --split val
```

By default, the simulator reads split CSVs from `data/splits`, writes daily snapshots to `data/simulation`, uses the previous-day-demand-plus-safety-stock initial state and the fixed-quantity periodic reorder policy, and applies the default simulator assumptions. If `--policy-config-json` is omitted, that policy defaults to `fixed_order_quantity=40` and `review_interval_days=7`. The fixed reorder-point policy uses default `reorder_point=40` and `fixed_order_quantity=80`, where the default order quantity is a simple base amount plus the default safety stock. The fixed-target order-up-to policy uses default `base_target_level=40`, and its effective target is `base_target_level + safety_stock`. The forecast-driven order-up-to policy reads a saved forecast artifact and uses forecasted lead-time demand plus safety stock as its target.

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

Example forecast-driven simulator run:

```bash
python -m src.simulation.run_simulation \
  --item-id FOODS_3_080 \
  --store-id CA_1 \
  --split val \
  --policy forecast_driven_order_up_to \
  --policy-config-json '{"forecast_driven_order_up_to": {"forecast_name": "moving_average_7", "forecast_csv_path": "data/forecasts/m5_foods_3_080_ca_1/moving_average_7/default/val_forecasts.csv"}}'
```

Valid simulator flag values:
- `--split`: `train`, `val`, or `test`
- `--split-dir`: path to the directory containing saved split folders
- `--output-dir`: path to the directory where daily simulation snapshots should be written
- `--initial-state`: `dummy` or `prev_day_demand_plus_safety_stock`
- `--policy`: `dummy`, `fixed_quantity_periodic_reorder`, `fixed_reorder_point`, `fixed_target_order_up_to`, or `forecast_driven_order_up_to`
- `--policy-config-json`: optional JSON object keyed by policy name, such as `{"fixed_quantity_periodic_reorder": {"fixed_order_quantity": 40, "review_interval_days": 7}}`, `{"fixed_reorder_point": {"reorder_point": 50, "fixed_order_quantity": 90}}`, `{"fixed_target_order_up_to": {"base_target_level": 40}}`, or `{"forecast_driven_order_up_to": {"forecast_name": "moving_average_7", "forecast_csv_path": "data/forecasts/m5_foods_3_080_ca_1/moving_average_7/default/val_forecasts.csv"}}`
- `--lead-time-days`: integer
- `--safety-stock`: numeric value
- `--holding-cost`: numeric value
- `--stockout-penalty`: numeric value
