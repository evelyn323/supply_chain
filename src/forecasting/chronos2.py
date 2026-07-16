from __future__ import annotations

import os

import pandas as pd

from src.simulation.util.history import get_available_history

DEFAULT_CHRONOS2_MODEL_ID = "amazon/chronos-2"
DEFAULT_CHRONOS2_SERIES_ID = "series_0"


def _get_chronos2_pipeline_class():
    try:
        from chronos import Chronos2Pipeline
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "chronos-forecasting is required for chronos2 forecasting. "
            "Install the project environment from environment.yml first."
        ) from exc
    return Chronos2Pipeline


def get_chronos2_forecast_name(
) -> str:
    return "chronos2"


def load_chronos2_pipeline():
    Chronos2Pipeline = _get_chronos2_pipeline_class()
    model_id = os.getenv("CHRONOS2_MODEL_ID", DEFAULT_CHRONOS2_MODEL_ID)
    device_map = os.getenv("CHRONOS2_DEVICE_MAP")
    if device_map:
        return Chronos2Pipeline.from_pretrained(model_id, device_map=device_map)
    return Chronos2Pipeline.from_pretrained(model_id)


def _normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized["date"] = pd.to_datetime(normalized["date"])
    return normalized.sort_values(by="date", ascending=True).reset_index(drop=True)


def _build_context_df(available_history: pd.DataFrame) -> pd.DataFrame:
    context_df = available_history[["date", "demand"]].copy()
    context_df = context_df.rename(columns={"date": "timestamp", "demand": "target"})
    context_df["id"] = DEFAULT_CHRONOS2_SERIES_ID
    return context_df[["id", "timestamp", "target"]]


def _build_bounded_context_df(
    available_history: pd.DataFrame,
    context_window_days: int,
) -> pd.DataFrame:
    if context_window_days <= 0:
        raise ValueError("context_window_days must be positive")
    return _build_context_df(available_history.tail(context_window_days))


def _get_prediction_column(prediction_df: pd.DataFrame) -> str:
    if "predictions" in prediction_df.columns:
        return "predictions"
    if "prediction" in prediction_df.columns:
        return "prediction"
    raise ValueError("Chronos2 forecast output must include a predictions column")


def build_chronos2_forecasts(
    pipeline,
    history_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    max_horizon_days: int,
    context_window_days: int,
) -> pd.DataFrame:
    if max_horizon_days <= 0:
        raise ValueError("max_horizon_days must be positive")
    if context_window_days <= 0:
        raise ValueError("context_window_days must be positive")

    history_df = _normalize_frame(history_df)
    eval_df = _normalize_frame(eval_df)

    forecast_rows: list[dict[str, object]] = []
    for row in eval_df.itertuples(index=False):
        forecast_origin_date = row.date
        available_history = get_available_history(history_df, eval_df, forecast_origin_date)
        if len(available_history) < context_window_days:
            continue

        prediction_df = pipeline.predict_df(
            _build_bounded_context_df(
                available_history=available_history,
                context_window_days=context_window_days,
            ),
            prediction_length=max_horizon_days,
            id_column="id",
            timestamp_column="timestamp",
            target="target",
        )
        prediction_df = prediction_df[prediction_df["id"] == DEFAULT_CHRONOS2_SERIES_ID].copy()
        prediction_df["timestamp"] = pd.to_datetime(prediction_df["timestamp"])
        prediction_df = prediction_df.sort_values(by="timestamp", ascending=True).reset_index(drop=True)
        prediction_column = _get_prediction_column(prediction_df)

        if len(prediction_df) < max_horizon_days:
            raise ValueError(
                "Chronos2 returned fewer forecast rows than the requested save horizon"
            )

        for horizon_day, prediction_row in enumerate(
            prediction_df.head(max_horizon_days).itertuples(index=False),
            start=1,
        ):
            forecast_rows.append(
                {
                    "forecast_origin_date": forecast_origin_date,
                    "target_date": prediction_row.timestamp,
                    "horizon_day": horizon_day,
                    "predicted_demand": float(getattr(prediction_row, prediction_column)),
                }
            )

    return pd.DataFrame(
        forecast_rows,
        columns=[
            "forecast_origin_date",
            "target_date",
            "horizon_day",
            "predicted_demand",
        ],
    )
