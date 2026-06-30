from __future__ import annotations

import pandas as pd

from src.simulation.types import InitialStateOption, SimulationConfig, SimulatorState


def init_simulator_state(
    history_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    config: SimulationConfig,
) -> SimulatorState:
    if config.initial_state_config.option is InitialStateOption.DUMMY:
        return init_dummy_state(history_df, eval_df)
    if config.initial_state_config.option is InitialStateOption.PREV_DAY_DEMAND_PLUS_SAFETY_STOCK:
        return init_prev_day_demand_plus_safety_stock_state(history_df, eval_df, config)

    raise ValueError(f"Unsupported initial-state option: {config.initial_state_config.option}")


def init_dummy_state(
    history_df: pd.DataFrame,
    eval_df: pd.DataFrame,
) -> SimulatorState:
    _ = history_df
    return SimulatorState(
        current_date=eval_df.iloc[0]["date"],
        on_hand_inventory=0.0,
    )


def init_prev_day_demand_plus_safety_stock_state(
    history_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    config: SimulationConfig,
) -> SimulatorState:
    if history_df.empty:
        raise ValueError("Previous-day-demand initial state requires at least one history row")

    history_df = history_df.copy()
    history_df["date"] = pd.to_datetime(history_df["date"])
    history_df = history_df.sort_values(by="date", ascending=True)
    prev_day_demand = float(history_df.iloc[-1]["demand"])

    return SimulatorState(
        current_date=pd.to_datetime(eval_df.iloc[0]["date"]),
        on_hand_inventory=prev_day_demand + config.assumptions.safety_stock,
    )
