from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.simulation.policy import decide_replenishment
from src.simulation.policy_configs import get_policy_config
from src.simulation.types import (
    InitialStateConfig,
    InitialStateOption,
    OutstandingOrder,
    PolicyOption,
    SimulationAssumptions,
    SimulationConfig,
    SimulatorState,
)


def test_fixed_quantity_periodic_reorder_orders_on_first_review_day() -> None:
    available_history = pd.DataFrame(columns=["date", "demand"])
    config = SimulationConfig(
        initial_state_config=InitialStateConfig(option=InitialStateOption.DUMMY),
        policy_config=get_policy_config(
            PolicyOption.FIXED_QUANTITY_PERIODIC_REORDER,
            overrides={
                PolicyOption.FIXED_QUANTITY_PERIODIC_REORDER.value: {
                    "fixed_order_quantity": 40.0,
                    "review_interval_days": 7,
                }
            },
        ),
        assumptions=SimulationAssumptions(),
    )
    state = SimulatorState(
        current_date=pd.Timestamp("2024-01-01"),
        on_hand_inventory=10.0,
    )

    order_quantity = decide_replenishment(available_history, state, config)

    assert order_quantity == 40.0


def test_fixed_quantity_periodic_reorder_skips_non_review_day() -> None:
    available_history = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=6, freq="D"),
            "demand": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        }
    )
    config = SimulationConfig(
        initial_state_config=InitialStateConfig(option=InitialStateOption.DUMMY),
        policy_config=get_policy_config(
            PolicyOption.FIXED_QUANTITY_PERIODIC_REORDER,
            overrides={
                PolicyOption.FIXED_QUANTITY_PERIODIC_REORDER.value: {
                    "fixed_order_quantity": 40.0,
                    "review_interval_days": 7,
                }
            },
        ),
        assumptions=SimulationAssumptions(),
    )
    state = SimulatorState(
        current_date=pd.Timestamp("2024-01-07"),
        on_hand_inventory=10.0,
    )

    order_quantity = decide_replenishment(available_history, state, config)

    assert order_quantity == 0.0


def test_fixed_reorder_point_orders_fixed_quantity_below_threshold() -> None:
    available_history = pd.DataFrame(columns=["date", "demand"])
    config = SimulationConfig(
        initial_state_config=InitialStateConfig(option=InitialStateOption.DUMMY),
        policy_config=get_policy_config(
            PolicyOption.FIXED_REORDER_POINT,
            overrides={
                PolicyOption.FIXED_REORDER_POINT.value: {
                    "reorder_point": 50.0,
                    "fixed_order_quantity": 80.0,
                }
            },
        ),
        assumptions=SimulationAssumptions(),
    )
    state = SimulatorState(
        current_date=pd.Timestamp("2024-01-01"),
        on_hand_inventory=10.0,
    )

    order_quantity = decide_replenishment(available_history, state, config)

    assert order_quantity == 80.0


def test_fixed_reorder_point_skips_when_inventory_position_meets_threshold() -> None:
    available_history = pd.DataFrame(columns=["date", "demand"])
    config = SimulationConfig(
        initial_state_config=InitialStateConfig(option=InitialStateOption.DUMMY),
        policy_config=get_policy_config(
            PolicyOption.FIXED_REORDER_POINT,
            overrides={
                PolicyOption.FIXED_REORDER_POINT.value: {
                    "reorder_point": 50.0,
                    "fixed_order_quantity": 80.0,
                }
            },
        ),
        assumptions=SimulationAssumptions(),
    )
    state = SimulatorState(
        current_date=pd.Timestamp("2024-01-01"),
        on_hand_inventory=10.0,
        outstanding_orders=[
            OutstandingOrder(
                quantity=40.0,
                arrival_date=pd.Timestamp("2024-01-02"),
            ),
        ],
    )

    order_quantity = decide_replenishment(available_history, state, config)

    assert order_quantity == 0.0


def test_fixed_target_order_up_to_orders_gap_to_target() -> None:
    available_history = pd.DataFrame(columns=["date", "demand"])
    config = SimulationConfig(
        initial_state_config=InitialStateConfig(option=InitialStateOption.DUMMY),
        policy_config=get_policy_config(
            PolicyOption.FIXED_TARGET_ORDER_UP_TO,
            overrides={
                PolicyOption.FIXED_TARGET_ORDER_UP_TO.value: {
                    "base_target_level": 40.0,
                }
            },
        ),
        assumptions=SimulationAssumptions(safety_stock=40.0),
    )
    state = SimulatorState(
        current_date=pd.Timestamp("2024-01-01"),
        on_hand_inventory=10.0,
    )

    order_quantity = decide_replenishment(available_history, state, config)

    assert order_quantity == 70.0


def test_fixed_target_order_up_to_skips_when_inventory_position_meets_target() -> None:
    available_history = pd.DataFrame(columns=["date", "demand"])
    config = SimulationConfig(
        initial_state_config=InitialStateConfig(option=InitialStateOption.DUMMY),
        policy_config=get_policy_config(
            PolicyOption.FIXED_TARGET_ORDER_UP_TO,
            overrides={
                PolicyOption.FIXED_TARGET_ORDER_UP_TO.value: {
                    "base_target_level": 40.0,
                }
            },
        ),
        assumptions=SimulationAssumptions(safety_stock=40.0),
    )
    state = SimulatorState(
        current_date=pd.Timestamp("2024-01-01"),
        on_hand_inventory=30.0,
        outstanding_orders=[
            OutstandingOrder(
                quantity=50.0,
                arrival_date=pd.Timestamp("2024-01-02"),
            ),
        ],
    )

    order_quantity = decide_replenishment(available_history, state, config)

    assert order_quantity == 0.0


def test_forecast_driven_order_up_to_reads_saved_forecast_artifact(tmp_path) -> None:
    forecast_csv_path = tmp_path / "val_forecasts.csv"
    pd.DataFrame(
        {
            "forecast_origin_date": ["2024-01-03", "2024-01-03", "2024-01-03"],
            "target_date": ["2024-01-03", "2024-01-04", "2024-01-05"],
            "horizon_day": [1, 2, 3],
            "predicted_demand": [6.0, 7.0, 8.0],
        }
    ).to_csv(forecast_csv_path, index=False)
    available_history = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=2, freq="D"),
            "demand": [3.0, 4.0],
        }
    )
    config = SimulationConfig(
        initial_state_config=InitialStateConfig(option=InitialStateOption.DUMMY),
        policy_config=get_policy_config(
            PolicyOption.FORECAST_DRIVEN_ORDER_UP_TO,
            overrides={
                PolicyOption.FORECAST_DRIVEN_ORDER_UP_TO.value: {
                    "forecast_name": "naive_last_value",
                    "forecast_csv_path": str(forecast_csv_path),
                }
            },
        ),
        assumptions=SimulationAssumptions(lead_time_days=2, safety_stock=10.0),
    )
    state = SimulatorState(
        current_date=pd.Timestamp("2024-01-03"),
        on_hand_inventory=5.0,
    )

    order_quantity = decide_replenishment(available_history, state, config)

    assert order_quantity == 20.0


def test_forecast_driven_policy_config_defaults_context_window_days_to_seven() -> None:
    policy_config = get_policy_config(
        PolicyOption.FORECAST_DRIVEN_ORDER_UP_TO,
        overrides={
            PolicyOption.FORECAST_DRIVEN_ORDER_UP_TO.value: {
                "forecast_name": "moving_average_7",
                "forecast_csv_path": "data/forecasts/example.csv",
            }
        },
    )

    assert policy_config.history_needed == 7
    assert policy_config.overrides["context_window_days"] == 7


def test_forecast_driven_policy_config_uses_explicit_context_window_days() -> None:
    policy_config = get_policy_config(
        PolicyOption.FORECAST_DRIVEN_ORDER_UP_TO,
        overrides={
            PolicyOption.FORECAST_DRIVEN_ORDER_UP_TO.value: {
                "forecast_name": "xgboost_recursive_7",
                "forecast_csv_path": "data/forecasts/example.csv",
                "context_window_days": 14,
            }
        },
    )

    assert policy_config.history_needed == 28


def test_forecast_driven_policy_config_sets_chronos2_history_needed_from_context_window() -> None:
    policy_config = get_policy_config(
        PolicyOption.FORECAST_DRIVEN_ORDER_UP_TO,
        overrides={
            PolicyOption.FORECAST_DRIVEN_ORDER_UP_TO.value: {
                "forecast_name": "chronos2",
                "forecast_csv_path": "data/forecasts/example.csv",
                "context_window_days": 7,
            }
        },
    )

    assert policy_config.history_needed == 7


def test_forecast_driven_policy_config_rejects_invalid_context_window_days() -> None:
    with pytest.raises(ValueError, match="context_window_days must be a positive integer"):
        get_policy_config(
            PolicyOption.FORECAST_DRIVEN_ORDER_UP_TO,
            overrides={
                PolicyOption.FORECAST_DRIVEN_ORDER_UP_TO.value: {
                    "forecast_name": "chronos2",
                    "forecast_csv_path": "data/forecasts/example.csv",
                    "context_window_days": 0,
                }
            },
        )
