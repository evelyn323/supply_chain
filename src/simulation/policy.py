from __future__ import annotations

import pandas as pd

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


def is_review_day(
    available_history: pd.DataFrame,
    review_interval_days: int,
) -> bool:
    # Use the count of prior observed days so review cadence stays chronological
    # even when a validation/test run starts with pre-existing history.
    day_index = len(available_history)
    return day_index % review_interval_days == 0
