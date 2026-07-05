from __future__ import annotations

from enum import Enum


class ForecastOption(str, Enum):
    NAIVE_LAST_VALUE = "naive_last_value"
