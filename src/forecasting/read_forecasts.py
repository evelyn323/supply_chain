from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd


@lru_cache(maxsize=None)
def load_forecasts(
    forecast_csv_path: str,
) -> pd.DataFrame:
    forecast_df = pd.read_csv(forecast_csv_path)
    required_columns = {
        "forecast_origin_date",
        "target_date",
        "horizon_day",
        "predicted_demand",
    }
    missing_columns = required_columns.difference(forecast_df.columns)
    if missing_columns:
        raise ValueError(
            f"Forecast file {forecast_csv_path} is missing required columns: {sorted(missing_columns)}"
        )

    forecast_df = forecast_df.copy()
    forecast_df["forecast_origin_date"] = pd.to_datetime(forecast_df["forecast_origin_date"])
    forecast_df["target_date"] = pd.to_datetime(forecast_df["target_date"])
    return forecast_df.sort_values(
        by=["forecast_origin_date", "target_date"],
        ascending=True,
    ).reset_index(drop=True)


def get_forecasted_demand(
    forecast_csv_path: Path,
    forecast_origin_date: pd.Timestamp,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.DataFrame:
    forecast_df = load_forecasts(str(forecast_csv_path.resolve()))
    origin_forecast_df = forecast_df[forecast_df["forecast_origin_date"] == forecast_origin_date]
    if origin_forecast_df.empty:
        raise ValueError(
            "Forecast file is missing forecast rows for origin date "
            f"{forecast_origin_date.date()} at {forecast_csv_path}"
        )
    date_range_forecast_df = origin_forecast_df[
        (origin_forecast_df["target_date"] >= start_date)
        & (origin_forecast_df["target_date"] <= end_date)
    ].copy()

    expected_target_dates = pd.date_range(start=start_date, end=end_date, freq="D")
    missing_target_dates = sorted(
        set(expected_target_dates).difference(date_range_forecast_df["target_date"])
    )
    if missing_target_dates:
        raise ValueError(
            "Forecast file is missing required target dates for "
            f"{forecast_origin_date.date()}: {[date.date().isoformat() for date in missing_target_dates]}"
        )

    return date_range_forecast_df.sort_values(by="target_date", ascending=True)
