from __future__ import annotations

import pandas as pd

from src.simulation.types import InitialStateOption, SimulationConfig, SimulatorState


def init_simulator_state(
    history_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    config: SimulationConfig,
) -> SimulatorState:
    if config.initial_state_config.option is InitialStateOption.DUMMY:
        # TODO: Replace the dummy zero-inventory start with the chosen initial-state rule.
        # 1. on hand inventory is fixed, policy specific, historical avg etc.
        # 2. outstanding orders is empty or if policy needs initial pipeline
        # 3. if history used, what to do if not enough history available
        return init_dummy_state(history_df, eval_df)

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
