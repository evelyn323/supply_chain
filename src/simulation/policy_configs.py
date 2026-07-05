from __future__ import annotations

from collections.abc import Mapping

from src.forecasting.types import ForecastOption
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
    if option is PolicyOption.FIXED_REORDER_POINT:
        reorder_point = policy_overrides.get("reorder_point", 40.0)
        fixed_order_quantity = policy_overrides.get("fixed_order_quantity", 80.0)
        if reorder_point < 0:
            raise ValueError("reorder_point must be non-negative")
        if fixed_order_quantity <= 0:
            raise ValueError("fixed_order_quantity must be positive")
        return PolicyConfig(
            option=option,
            history_needed=0,
            overrides={
                "reorder_point": reorder_point,
                "fixed_order_quantity": fixed_order_quantity,
            },
        )
    if option is PolicyOption.FIXED_TARGET_ORDER_UP_TO:
        base_target_level = policy_overrides.get("base_target_level", 40.0)
        if base_target_level < 0:
            raise ValueError("base_target_level must be non-negative")
        return PolicyConfig(
            option=option,
            history_needed=0,
            overrides={
                "base_target_level": base_target_level,
            },
        )
    if option is PolicyOption.FORECAST_DRIVEN_ORDER_UP_TO:
        forecast_name = policy_overrides.get(
            "forecast_name",
            ForecastOption.NAIVE_LAST_VALUE.value,
        )
        forecast_csv_path = policy_overrides.get("forecast_csv_path")
        if forecast_name not in {option.value for option in ForecastOption}:
            raise ValueError(f"Unsupported forecast_name: {forecast_name}")
        if forecast_csv_path is None:
            return PolicyConfig(
                option=option,
                history_needed=1,
                overrides={
                    "forecast_name": forecast_name,
                },
            )
        if not isinstance(forecast_csv_path, str) or not forecast_csv_path:
            raise ValueError("forecast_csv_path must be a non-empty string")
        return PolicyConfig(
            option=option,
            history_needed=1,
            overrides={
                "forecast_name": forecast_name,
                "forecast_csv_path": forecast_csv_path,
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
