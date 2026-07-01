from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.simulation.policy import decide_replenishment
from src.simulation.policy_configs import get_policy_config
from src.simulation.types import (
    InitialStateConfig,
    InitialStateOption,
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
