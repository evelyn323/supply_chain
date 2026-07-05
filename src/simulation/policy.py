from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.forecasting.read_forecasts import get_forecasted_demand
from src.simulation.types import PolicyOption, SimulationConfig, SimulatorState


def decide_replenishment(
    available_history: pd.DataFrame,
    state: SimulatorState,
    config: SimulationConfig,
) -> float:
    if config.policy_config.option is PolicyOption.DUMMY:
        return decide_dummy_replenishment(available_history, state)
    if config.policy_config.option is PolicyOption.FIXED_QUANTITY_PERIODIC_REORDER:
        return decide_fixed_quantity_periodic_replenishment(available_history, state, config)
    if config.policy_config.option is PolicyOption.FIXED_REORDER_POINT:
        return decide_fixed_reorder_point_replenishment(state, config)
    if config.policy_config.option is PolicyOption.FIXED_TARGET_ORDER_UP_TO:
        return decide_fixed_target_order_up_to_replenishment(state, config)
    if config.policy_config.option is PolicyOption.FORECAST_DRIVEN_ORDER_UP_TO:
        return decide_forecast_driven_order_up_to_replenishment(state, config)

    raise ValueError(f"Unsupported policy option: {config.policy_config.option}")


def decide_dummy_replenishment(
    available_history: pd.DataFrame,
    state: SimulatorState,
) -> float:
    _ = available_history
    _ = state
    return 0.0


def decide_fixed_quantity_periodic_replenishment(
    available_history: pd.DataFrame,
    state: SimulatorState,
    config: SimulationConfig,
) -> float:
    review_interval_days = config.policy_config.overrides.get("review_interval_days")
    fixed_order_quantity = config.policy_config.overrides.get("fixed_order_quantity")

    if review_interval_days is None or fixed_order_quantity is None:
        raise ValueError("Fixed-quantity periodic reorder policy is missing required parameters")

    _ = state
    if not is_review_day(available_history, review_interval_days):
        return 0.0
    return fixed_order_quantity


def decide_fixed_reorder_point_replenishment(
    state: SimulatorState,
    config: SimulationConfig,
) -> float:
    reorder_point = config.policy_config.overrides.get("reorder_point")
    fixed_order_quantity = config.policy_config.overrides.get("fixed_order_quantity")

    if reorder_point is None or fixed_order_quantity is None:
        raise ValueError("Fixed reorder-point policy is missing required parameters")

    if get_inventory_position(state) >= reorder_point:
        return 0.0
    return fixed_order_quantity


def decide_fixed_target_order_up_to_replenishment(
    state: SimulatorState,
    config: SimulationConfig,
) -> float:
    base_target_level = config.policy_config.overrides.get("base_target_level")

    if base_target_level is None:
        raise ValueError("Fixed target order-up-to policy is missing required parameters")

    order_up_to_level = base_target_level + config.assumptions.safety_stock
    inventory_position = get_inventory_position(state)
    if inventory_position >= order_up_to_level:
        return 0.0
    return order_up_to_level - inventory_position


def decide_forecast_driven_order_up_to_replenishment(
    state: SimulatorState,
    config: SimulationConfig,
) -> float:
    forecast_csv_path = config.policy_config.overrides.get("forecast_csv_path")

    if forecast_csv_path is None:
        raise ValueError("Forecast-driven order-up-to policy is missing required parameters")

    lead_time_forecast_df = get_forecasted_demand(
        forecast_csv_path=Path(str(forecast_csv_path)),
        forecast_origin_date=state.current_date,
        start_date=state.current_date + pd.Timedelta(days=1),
        end_date=state.current_date + pd.Timedelta(days=config.assumptions.lead_time_days),
    )
    forecasted_lead_time_demand = float(lead_time_forecast_df["predicted_demand"].sum())
    order_up_to_level = forecasted_lead_time_demand + config.assumptions.safety_stock
    inventory_position = get_inventory_position(state)
    if inventory_position >= order_up_to_level:
        return 0.0
    return order_up_to_level - inventory_position


def get_inventory_position(state: SimulatorState) -> float:
    outstanding_quantity = sum(order.quantity for order in state.outstanding_orders)
    return state.on_hand_inventory + outstanding_quantity


def is_review_day(
    available_history: pd.DataFrame,
    review_interval_days: int,
) -> bool:
    # Use the count of prior observed days so review cadence stays chronological
    # even when a validation/test run starts with pre-existing history.
    day_index = len(available_history)
    return day_index % review_interval_days == 0
