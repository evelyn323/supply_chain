from __future__ import annotations

from enum import Enum


class ForecastOption(str, Enum):
    NAIVE_LAST_VALUE = "naive_last_value"
    MOVING_AVERAGE = "moving_average"
    CHRONOS2 = "chronos2"
    XGBOOST_RECURSIVE = "xgboost_recursive"
