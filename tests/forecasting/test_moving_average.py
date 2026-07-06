from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.forecasting.moving_average import build_moving_average_forecasts


def test_build_moving_average_forecasts_uses_trailing_window_mean() -> None:
    history_df = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "demand": [2.0, 4.0, 6.0],
        }
    )
    eval_df = pd.DataFrame(
        {
            "date": ["2024-01-04", "2024-01-05"],
            "demand": [8.0, 10.0],
        }
    )

    forecast_df = build_moving_average_forecasts(
        history_df=history_df,
        eval_df=eval_df,
        max_horizon_days=2,
        context_window_days=2,
    )

    assert forecast_df["forecast_origin_date"].tolist() == [
        pd.Timestamp("2024-01-04"),
        pd.Timestamp("2024-01-04"),
        pd.Timestamp("2024-01-05"),
        pd.Timestamp("2024-01-05"),
    ]
    assert forecast_df["predicted_demand"].tolist() == [5.0, 5.0, 7.0, 7.0]


def test_build_moving_average_forecasts_skips_until_enough_history() -> None:
    history_df = pd.DataFrame(
        {
            "date": ["2024-01-01"],
            "demand": [2.0],
        }
    )
    eval_df = pd.DataFrame(
        {
            "date": ["2024-01-02"],
            "demand": [4.0],
        }
    )

    forecast_df = build_moving_average_forecasts(
        history_df=history_df,
        eval_df=eval_df,
        max_horizon_days=2,
        context_window_days=2,
    )

    assert forecast_df.empty
