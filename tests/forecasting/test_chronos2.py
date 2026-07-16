from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.forecasting.chronos2 import (
    build_chronos2_forecasts,
    get_chronos2_forecast_name,
)


class DummyChronos2Pipeline:
    def __init__(self) -> None:
        self.seen_contexts: list[pd.DataFrame] = []

    def predict_df(
        self,
        context_df: pd.DataFrame,
        prediction_length: int,
        id_column: str,
        timestamp_column: str,
        target: str,
    ) -> pd.DataFrame:
        self.seen_contexts.append(context_df.copy())
        last_timestamp = pd.to_datetime(context_df[timestamp_column]).max()
        last_target = float(context_df[target].iloc[-1])
        return pd.DataFrame(
            {
                id_column: [context_df[id_column].iloc[0]] * prediction_length,
                timestamp_column: pd.date_range(
                    last_timestamp + pd.Timedelta(days=1),
                    periods=prediction_length,
                    freq="D",
                ),
                "predictions": [
                    last_target + float(horizon_day)
                    for horizon_day in range(1, prediction_length + 1)
                ],
            }
        )


def test_build_chronos2_forecasts_saves_direct_multi_step_predictions() -> None:
    history_df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=7, freq="D"),
            "demand": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
        }
    )
    eval_df = pd.DataFrame(
        {
            "date": ["2024-01-08", "2024-01-09"],
            "demand": [8.0, 9.0],
        }
    )

    pipeline = DummyChronos2Pipeline()
    forecast_df = build_chronos2_forecasts(
        pipeline=pipeline,
        history_df=history_df,
        eval_df=eval_df,
        max_horizon_days=2,
        context_window_days=7,
    )

    assert forecast_df["forecast_origin_date"].tolist() == [
        pd.Timestamp("2024-01-08"),
        pd.Timestamp("2024-01-08"),
        pd.Timestamp("2024-01-09"),
        pd.Timestamp("2024-01-09"),
    ]
    assert forecast_df["target_date"].tolist() == [
        pd.Timestamp("2024-01-08"),
        pd.Timestamp("2024-01-09"),
        pd.Timestamp("2024-01-09"),
        pd.Timestamp("2024-01-10"),
    ]
    assert forecast_df["predicted_demand"].tolist() == [8.0, 9.0, 9.0, 10.0]
    assert len(pipeline.seen_contexts) == 2


def test_build_chronos2_forecasts_requests_full_required_horizon() -> None:
    pipeline = DummyChronos2Pipeline()
    forecast_df = build_chronos2_forecasts(
        pipeline=pipeline,
        history_df=pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=7, freq="D"),
                "demand": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
            }
        ),
        eval_df=pd.DataFrame({"date": ["2024-01-08"], "demand": [8.0]}),
        max_horizon_days=8,
        context_window_days=7,
    )

    assert forecast_df["horizon_day"].tolist() == [1, 2, 3, 4, 5, 6, 7, 8]
    assert len(forecast_df) == 8
    assert forecast_df["predicted_demand"].tolist() == [8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0]


def test_get_chronos2_forecast_name_is_deterministic() -> None:
    assert get_chronos2_forecast_name() == "chronos2"


def test_build_chronos2_forecasts_uses_trailing_context_window() -> None:
    history_df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=5, freq="D"),
            "demand": [1.0, 2.0, 3.0, 4.0, 5.0],
        }
    )
    eval_df = pd.DataFrame(
        {
            "date": ["2024-01-06"],
            "demand": [6.0],
        }
    )

    pipeline = DummyChronos2Pipeline()
    build_chronos2_forecasts(
        pipeline=pipeline,
        history_df=history_df,
        eval_df=eval_df,
        max_horizon_days=2,
        context_window_days=3,
    )

    seen_context = pipeline.seen_contexts[0]
    assert pd.to_datetime(seen_context["timestamp"]).tolist() == [
        pd.Timestamp("2024-01-03"),
        pd.Timestamp("2024-01-04"),
        pd.Timestamp("2024-01-05"),
    ]
    assert seen_context["target"].tolist() == [3.0, 4.0, 5.0]


def test_build_chronos2_forecasts_skips_until_context_window_is_available() -> None:
    history_df = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02"],
            "demand": [3.0, 4.0],
        }
    )
    eval_df = pd.DataFrame(
        {
            "date": ["2024-01-03", "2024-01-04"],
            "demand": [5.0, 6.0],
        }
    )

    pipeline = DummyChronos2Pipeline()
    forecast_df = build_chronos2_forecasts(
        pipeline=pipeline,
        history_df=history_df,
        eval_df=eval_df,
        max_horizon_days=2,
        context_window_days=7,
    )

    assert forecast_df.empty
    assert pipeline.seen_contexts == []
