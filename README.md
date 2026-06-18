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
- `notebooks`: exploratory Jupyter notebooks for dataset inspection, EDA, and early prototyping before logic is moved into reusable Python modules

## Setup and Usage
The project uses a Conda environment defined in [environment.yml](/Users/evelynchou/Desktop/School/Personal_Projects/supply_chain/environment.yml).

```bash
conda env create -f environment.yml
conda activate supply-chain
```
