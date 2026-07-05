from __future__ import annotations

import pandas as pd

from src.simulation.util.history import get_available_history


def build_naive_last_value_forecasts(
    history_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    max_horizon_days: int,
) -> pd.DataFrame:
    if max_horizon_days <= 0:
        raise ValueError("max_horizon_days must be positive")

    history_df = history_df.copy()
    eval_df = eval_df.copy()
    history_df["date"] = pd.to_datetime(history_df["date"])
    eval_df["date"] = pd.to_datetime(eval_df["date"])
    history_df = history_df.sort_values(by="date", ascending=True)
    eval_df = eval_df.sort_values(by="date", ascending=True)

    forecast_rows: list[dict[str, object]] = []
    for row in eval_df.itertuples(index=False):
        forecast_origin_date = row.date
        available_history = get_available_history(history_df, eval_df, forecast_origin_date)
        if available_history.empty:
            continue

        last_observed_demand = float(available_history.iloc[-1]["demand"])
        for horizon_day in range(1, max_horizon_days + 1):
            forecast_rows.append(
                {
                    "forecast_origin_date": forecast_origin_date,
                    "target_date": forecast_origin_date + pd.Timedelta(days=horizon_day),
                    "horizon_day": horizon_day,
                    "predicted_demand": last_observed_demand,
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
