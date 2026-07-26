from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data.types import DataSplit, SKU
from src.forecasting.naive_last_value import build_naive_last_value_forecasts
from src.forecasting.read_forecasts import get_forecasted_demand
from src.forecasting.save_forecasts import build_forecast_csv_path, save_forecasts


def test_build_naive_last_value_forecasts_uses_last_observed_demand() -> None:
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

    forecast_df = build_naive_last_value_forecasts(
        history_df=history_df,
        eval_df=eval_df,
        max_horizon_days=2,
    )

    assert forecast_df["forecast_origin_date"].tolist() == [
        pd.Timestamp("2024-01-03"),
        pd.Timestamp("2024-01-03"),
        pd.Timestamp("2024-01-04"),
        pd.Timestamp("2024-01-04"),
    ]
    assert forecast_df["target_date"].tolist() == [
        pd.Timestamp("2024-01-03"),
        pd.Timestamp("2024-01-04"),
        pd.Timestamp("2024-01-04"),
        pd.Timestamp("2024-01-05"),
    ]
    assert forecast_df["predicted_demand"].tolist() == [4.0, 4.0, 5.0, 5.0]


def test_save_and_read_forecasts_support_date_range_queries(tmp_path) -> None:
    forecast_df = pd.DataFrame(
        {
            "forecast_origin_date": ["2024-01-03", "2024-01-03", "2024-01-03"],
            "target_date": ["2024-01-03", "2024-01-04", "2024-01-05"],
            "horizon_day": [1, 2, 3],
            "predicted_demand": [4.0, 4.0, 4.0],
        }
    )
    output_path = build_forecast_csv_path(
        output_dir=tmp_path,
        sku=SKU("FOODS_3_080", "CA_1"),
        forecast_name="naive_last_value",
        split=DataSplit.VAL,
    )

    save_forecasts(forecast_df, output_path)
    loaded_range_df = get_forecasted_demand(
        forecast_csv_path=output_path,
        forecast_origin_date=pd.Timestamp("2024-01-03"),
        start_date=pd.Timestamp("2024-01-03"),
        end_date=pd.Timestamp("2024-01-04"),
    )

    assert output_path == Path(
        tmp_path
        / "m5_foods_3_080_ca_1/naive_last_value/default/val_forecasts.csv"
    )
    assert loaded_range_df["target_date"].tolist() == [
        pd.Timestamp("2024-01-03"),
        pd.Timestamp("2024-01-04"),
    ]
    assert loaded_range_df["predicted_demand"].tolist() == [4.0, 4.0]
