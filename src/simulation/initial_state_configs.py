from __future__ import annotations

from src.simulation.types import InitialStateConfig, InitialStateOption


def get_initial_state_config(option: InitialStateOption) -> InitialStateConfig:
    if option is InitialStateOption.DUMMY:
        return InitialStateConfig(option=option, history_needed=0)

    raise ValueError(f"Unsupported initial-state option: {option}")
