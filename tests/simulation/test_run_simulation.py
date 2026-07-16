from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.simulation.initial_state_configs import get_initial_state_config
from src.simulation.policy_configs import get_policy_config
from src.simulation.run_simulation import run_simulation
from src.simulation.util.paths import (
    build_assumption_profile_slug,
    build_policy_config_slug,
    build_snapshot_csv_path,
)
from src.simulation.types import (
    InitialStateOption,
    PolicyOption,
    SimulationAssumptions,
    SimulationConfig,
)
from src.data.types import SKU, DataSplit


def test_build_snapshot_csv_path_uses_policy_and_assumption_profile() -> None:
    sku = SKU("FOODS_3_080", "CA_1")

    default_path = build_snapshot_csv_path(
        Path("data/simulation"),
        sku,
        get_policy_config(PolicyOption.FIXED_QUANTITY_PERIODIC_REORDER),
        SimulationAssumptions(),
        DataSplit.VAL,
    )
    sensitivity_path = build_snapshot_csv_path(
        Path("data/simulation"),
        sku,
        get_policy_config(PolicyOption.FIXED_QUANTITY_PERIODIC_REORDER),
        SimulationAssumptions(lead_time_days=3),
        DataSplit.VAL,
    )
    override_path = build_snapshot_csv_path(
        Path("data/simulation"),
        sku,
        get_policy_config(
            PolicyOption.FIXED_TARGET_ORDER_UP_TO,
            overrides={
                PolicyOption.FIXED_TARGET_ORDER_UP_TO.value: {
                    "base_target_level": 80.0,
                }
            },
        ),
        SimulationAssumptions(),
        DataSplit.VAL,
    )
    forecast_path = build_snapshot_csv_path(
        Path("data/simulation"),
        sku,
        get_policy_config(
            PolicyOption.FORECAST_DRIVEN_ORDER_UP_TO,
            overrides={
                PolicyOption.FORECAST_DRIVEN_ORDER_UP_TO.value: {
                    "forecast_name": "naive_last_value",
                    "forecast_csv_path": "data/forecasts/m5_foods_3_080_ca_1/naive_last_value/default/val_forecasts.csv",
                }
            },
        ),
        SimulationAssumptions(),
        DataSplit.VAL,
    )

    assert default_path == Path(
        "data/simulation/m5_foods_3_080_ca_1/fixed_quantity_periodic_reorder/default/val_daily_snapshots.csv"
    )
    assert sensitivity_path == Path(
        "data/simulation/m5_foods_3_080_ca_1/fixed_quantity_periodic_reorder/lt_3_ss_40_hc_0.1_sp_2/val_daily_snapshots.csv"
    )
    assert override_path == Path(
        "data/simulation/m5_foods_3_080_ca_1/fixed_target_order_up_to/base-target-level_80/default/val_daily_snapshots.csv"
    )
    assert forecast_path == Path(
        "data/simulation/m5_foods_3_080_ca_1/forecast_driven_order_up_to/default/val_daily_snapshots.csv"
    )


def test_build_assumption_profile_slug_returns_default_for_default_assumptions() -> None:
    assert build_assumption_profile_slug(SimulationAssumptions()) == "default"


def test_build_policy_config_slug_returns_none_for_default_policy() -> None:
    assert build_policy_config_slug(get_policy_config(PolicyOption.FIXED_TARGET_ORDER_UP_TO)) is None


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


def test_run_simulation_shifts_eval_window_for_xgboost_history_requirement(tmp_path) -> None:
    history_df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=10, freq="D"),
            "demand": [5.0] * 10,
        }
    )
    eval_df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-11", periods=19, freq="D"),
            "demand": [6.0] * 19,
        }
    )
    forecast_csv_path = tmp_path / "xgboost_val_forecasts.csv"
    pd.DataFrame(
        {
            "forecast_origin_date": ["2024-01-28", "2024-01-28", "2024-01-29", "2024-01-29"],
            "target_date": ["2024-01-29", "2024-01-30", "2024-01-30", "2024-01-31"],
            "horizon_day": [1, 2, 1, 2],
            "predicted_demand": [7.0, 7.0, 7.0, 7.0],
        }
    ).to_csv(forecast_csv_path, index=False)
    config = SimulationConfig(
        initial_state_config=get_initial_state_config(InitialStateOption.DUMMY),
        policy_config=get_policy_config(
            PolicyOption.FORECAST_DRIVEN_ORDER_UP_TO,
            overrides={
                PolicyOption.FORECAST_DRIVEN_ORDER_UP_TO.value: {
                    "forecast_name": "xgboost_recursive_7",
                    "forecast_csv_path": str(forecast_csv_path),
                    "context_window_days": 7,
                }
            },
        ),
        assumptions=SimulationAssumptions(lead_time_days=2, safety_stock=0.0),
    )

    metrics = run_simulation(history_df, eval_df, config)

    assert metrics.eval_start_date == pd.Timestamp("2024-01-29")


def test_run_simulation_raises_when_forecast_rows_are_missing_after_history_shift(tmp_path) -> None:
    history_df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=10, freq="D"),
            "demand": [5.0] * 10,
        }
    )
    eval_df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-11", periods=20, freq="D"),
            "demand": [6.0] * 20,
        }
    )
    forecast_csv_path = tmp_path / "chronos_val_forecasts.csv"
    pd.DataFrame(
        {
            "forecast_origin_date": ["2024-01-17"],
            "target_date": ["2024-01-18"],
            "horizon_day": [1],
            "predicted_demand": [7.0],
        }
    ).to_csv(forecast_csv_path, index=False)
    config = SimulationConfig(
        initial_state_config=get_initial_state_config(InitialStateOption.DUMMY),
        policy_config=get_policy_config(
            PolicyOption.FORECAST_DRIVEN_ORDER_UP_TO,
            overrides={
                PolicyOption.FORECAST_DRIVEN_ORDER_UP_TO.value: {
                    "forecast_name": "chronos2",
                    "forecast_csv_path": str(forecast_csv_path),
                    "context_window_days": 7,
                }
            },
        ),
        assumptions=SimulationAssumptions(lead_time_days=2, safety_stock=0.0),
    )

    with pytest.raises(ValueError, match="Forecast file is missing forecast rows for origin date"):
        run_simulation(history_df, eval_df, config)
