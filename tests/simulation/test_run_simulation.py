from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.simulation.initial_state_configs import get_initial_state_config
from src.simulation.policy_configs import get_policy_config
from src.simulation.run_simulation import run_simulation
from src.simulation.types import (
    InitialStateOption,
    PolicyOption,
    SimulationAssumptions,
    SimulationConfig,
)


def test_run_simulation_dummy_pipeline_smoke(tmp_path) -> None:
    history_df = pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-01"],
            "demand": [4.0, 3.0],
        }
    )
    eval_df = pd.DataFrame(
        {
            "date": ["2024-01-05", "2024-01-03", "2024-01-04"],
            "demand": [7.0, 5.0, 6.0],
        }
    )
    config = SimulationConfig(
        initial_state_config=get_initial_state_config(InitialStateOption.DUMMY),
        policy_config=get_policy_config(PolicyOption.DUMMY),
        assumptions=SimulationAssumptions(
            lead_time_days=5,
            safety_stock=40.0,
            holding_cost=0.10,
            stockout_penalty=2.00,
        ),
    )
    snapshot_csv_path = tmp_path / "dummy_daily_snapshots.csv"

    metrics = run_simulation(
        history_df,
        eval_df,
        config,
        snapshot_csv_path=snapshot_csv_path,
    )

    snapshots = pd.read_csv(snapshot_csv_path)

    assert metrics.num_eval_days == 3
    assert metrics.eval_start_date == pd.Timestamp("2024-01-03")
    assert metrics.eval_end_date == pd.Timestamp("2024-01-05")
    assert metrics.total_demand == 18.0
    assert metrics.total_fulfilled_demand == 0.0
    assert metrics.total_unmet_demand == 18.0
    assert metrics.fill_rate == 0.0
    assert metrics.stockout_days == 3
    assert metrics.total_holding_cost == 0.0
    assert metrics.total_stockout_cost == 36.0
    assert metrics.total_cost == 36.0
    assert metrics.ending_inventory == 0.0

    assert len(snapshots) == metrics.num_eval_days
    assert snapshots["date"].tolist() == [
        "2024-01-03T00:00:00",
        "2024-01-04T00:00:00",
        "2024-01-05T00:00:00",
    ]
    assert snapshots["on_hand_inventory"].tolist() == [0.0, 0.0, 0.0]
    assert snapshots["fulfilled_demand"].tolist() == [0.0, 0.0, 0.0]
    assert snapshots["unmet_demand"].tolist() == [5.0, 6.0, 7.0]
    assert snapshots["stockout_day"].tolist() == [True, True, True]
    assert snapshots["outstanding_orders"].apply(json.loads).tolist() == [[], [], []]
    assert (
        snapshots["fulfilled_demand"] + snapshots["unmet_demand"]
        == snapshots["demand"]
    ).all()
    assert (snapshots["on_hand_inventory"] >= 0).all()
