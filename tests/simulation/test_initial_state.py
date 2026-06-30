from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.simulation.initial_state import init_simulator_state
from src.simulation.initial_state_configs import get_initial_state_config
from src.simulation.policy_configs import get_policy_config
from src.simulation.types import (
    InitialStateOption,
    PolicyOption,
    SimulationAssumptions,
    SimulationConfig,
)


def test_init_prev_day_demand_plus_safety_stock_uses_latest_history_row() -> None:
    history_df = pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-01"],
            "demand": [4.0, 3.0],
        }
    )
    eval_df = pd.DataFrame(
        {
            "date": ["2024-01-03"],
            "demand": [5.0],
        }
    )
    config = SimulationConfig(
        initial_state_config=get_initial_state_config(
            InitialStateOption.PREV_DAY_DEMAND_PLUS_SAFETY_STOCK
        ),
        policy_config=get_policy_config(PolicyOption.DUMMY),
        assumptions=SimulationAssumptions(safety_stock=40.0),
    )

    state = init_simulator_state(history_df, eval_df, config)

    assert state.current_date == pd.Timestamp("2024-01-03")
    assert state.on_hand_inventory == 44.0
    assert state.outstanding_orders == []
