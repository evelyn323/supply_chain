from __future__ import annotations

from src.simulation.types import PolicyConfig, PolicyOption


def get_policy_config(option: PolicyOption) -> PolicyConfig:
    if option is PolicyOption.DUMMY:
        return PolicyConfig(option=option, history_needed=0)

    raise ValueError(f"Unsupported policy option: {option}")
