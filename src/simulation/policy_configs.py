from __future__ import annotations

from collections.abc import Mapping
import re

from src.forecasting.types import ForecastOption
from src.simulation.types import PolicyConfig, PolicyOption

DEFAULT_FORECAST_CONTEXT_WINDOW_DAYS = 7
XGBOOST_MIN_HISTORY_DAYS = 28


def _get_required_positive_int(
    policy_overrides: Mapping[str, object],
    field_name: str,
) -> int:
    raw_value = policy_overrides.get(field_name)
    if not isinstance(raw_value, int) or raw_value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return raw_value


def _parse_window_from_suffix(
    forecast_name: str,
    prefix: str,
) -> int | None:
    match = re.fullmatch(rf"{re.escape(prefix)}_(\d+)", forecast_name)
    if match is None:
        return None
    return int(match.group(1))


def get_forecast_history_needed(
    forecast_name: str,
    context_window_days: int,
) -> int:
    if forecast_name == ForecastOption.NAIVE_LAST_VALUE.value:
        return 1
    if (
        forecast_name == ForecastOption.MOVING_AVERAGE.value
        or _parse_window_from_suffix(forecast_name, ForecastOption.MOVING_AVERAGE.value)
        is not None
    ):
        return context_window_days
    if (
        forecast_name == ForecastOption.XGBOOST_RECURSIVE.value
        or _parse_window_from_suffix(forecast_name, ForecastOption.XGBOOST_RECURSIVE.value)
        is not None
    ):
        return max(context_window_days, XGBOOST_MIN_HISTORY_DAYS)
    if forecast_name == ForecastOption.CHRONOS2.value:
        return context_window_days
    raise ValueError(f"Unsupported forecast_name: {forecast_name}")


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
        if not isinstance(forecast_name, str) or not forecast_name:
            raise ValueError("forecast_name must be a non-empty string")
        if not any(
            forecast_name == option.value or forecast_name.startswith(f"{option.value}_")
            for option in ForecastOption
        ):
            raise ValueError(f"Unsupported forecast_name: {forecast_name}")
        context_window_days = policy_overrides.get(
            "context_window_days",
            DEFAULT_FORECAST_CONTEXT_WINDOW_DAYS,
        )
        if not isinstance(context_window_days, int) or context_window_days <= 0:
            raise ValueError("context_window_days must be a positive integer")
        history_needed = get_forecast_history_needed(
            forecast_name,
            context_window_days,
        )
        if forecast_csv_path is None:
            return PolicyConfig(
                option=option,
                history_needed=history_needed,
                overrides={
                    "forecast_name": forecast_name,
                    "context_window_days": context_window_days,
                },
            )
        if not isinstance(forecast_csv_path, str) or not forecast_csv_path:
            raise ValueError("forecast_csv_path must be a non-empty string")
        config_overrides = {
            "forecast_name": forecast_name,
            "forecast_csv_path": forecast_csv_path,
            "context_window_days": context_window_days,
        }
        return PolicyConfig(
            option=option,
            history_needed=history_needed,
            overrides=config_overrides,
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
