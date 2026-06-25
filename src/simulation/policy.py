from __future__ import annotations

import pandas as pd

from src.simulation.types import SimulationConfig, SimulatorState


def decide_replenishment(
    available_history: pd.DataFrame,
    state: SimulatorState,
    config: SimulationConfig,
) -> float:
    # TODO: Dispatch to the chosen replenishment policy using config inputs.
    # TODO: Decide which policy parameters belong in SimulationConfig 
    _ = config
    # TODO: Replace the dummy no-order policy with the real policies.
    # 1. required lookback window/history. what to do if available history is too short (no order, fallback, error)
    # 2. decide what info each policy needs. inventory position, on-hand inventory, outstanding orders, demand history, forecast demand etc.
    # 3. policy returns only order quantity? how to document decision process
    return decide_dummy_replenishment(available_history, state)


def decide_dummy_replenishment(
    available_history: pd.DataFrame,
    state: SimulatorState,
) -> float:

    _ = available_history
    _ = state
    return 0.0
