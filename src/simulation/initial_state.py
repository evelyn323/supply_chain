from __future__ import annotations

import pandas as pd

from src.simulation.types import SimulationConfig, SimulatorState


def init_simulator_state(
    history_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    config: SimulationConfig,
) -> SimulatorState:
    # TODO: Dispatch to the chosen initialization rule using config/policy inputs.
    # TODO: Decide which initialization choices belong in SimulationConfig.
    _ = config
    # TODO: Replace the dummy zero-inventory start with the chosen initial-state rule.
    # 1. on hand inventory is fixed, policy specific, historical avg etc.
    # 2. outstanding orders is empty or if policy needs initial pipeline
    # 3. if history used, what to do if not enough history available
    return init_dummy_state(history_df, eval_df)


def init_dummy_state(
    history_df: pd.DataFrame,
    eval_df: pd.DataFrame,
) -> SimulatorState:
    _ = history_df
    return SimulatorState(
        current_date=eval_df.iloc[0]["date"],
        on_hand_inventory=0.0,
    )
