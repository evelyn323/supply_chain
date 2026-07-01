from __future__ import annotations

from collections.abc import Mapping

from src.simulation.types import PolicyConfig, PolicyOption


def get_policy_config(
    option: PolicyOption,
    overrides: Mapping[str, object] | None = None,
) -> PolicyConfig:
    overrides = overrides or {}
    policy_overrides = get_policy_overrides(option, overrides)

    if option is PolicyOption.DUMMY:
        return PolicyConfig(option=option, history_needed=0, overrides={})
    if option is PolicyOption.FIXED_QUANTITY_PERIODIC_REORDER:
        fixed_order_quantity = policy_overrides.get("fixed_order_quantity", 40.0)
        review_interval_days = policy_overrides.get("review_interval_days", 7)
        if fixed_order_quantity <= 0:
            raise ValueError("fixed_order_quantity must be positive")
        if review_interval_days <= 0:
            raise ValueError("review_interval_days must be positive")
        return PolicyConfig(
            option=option,
            history_needed=0,
            overrides={
                "fixed_order_quantity": fixed_order_quantity,
                "review_interval_days": review_interval_days,
            },
        )

    raise ValueError(f"Unsupported policy option: {option}")


def get_policy_overrides(
    option: PolicyOption,
    overrides: Mapping[str, object],
) -> Mapping[str, object]:
    raw_policy_overrides = overrides.get(option.value, {})
    if not isinstance(raw_policy_overrides, Mapping):
        raise ValueError(f"Policy overrides for {option.value} must be a JSON object")
    return raw_policy_overrides
