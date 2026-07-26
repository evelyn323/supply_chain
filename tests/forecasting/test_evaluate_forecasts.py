from __future__ import annotations

import math

import pandas as pd

from src.data.types import DataSplit, SKU
from src.forecasting.evaluate_forecasts import compute_rmse, load_actual_and_forecast_data
from src.forecasting.save_forecasts import build_forecast_csv_path, save_forecasts


def test_compute_rmse_scores_forecast_rows_with_matching_actual_dates() -> None:
    actual_df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
            "demand": [10.0, 14.0],
        }
    )
    forecast_df = pd.DataFrame(
        {
            "forecast_origin_date": ["2024-01-01", "2024-01-02", "2024-01-02"],
            "target_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "horizon_day": [1, 1, 2],
            "predicted_demand": [12.0, 13.0, 20.0],
        }
    )

    rmse, num_scored_rows = compute_rmse(actual_df, forecast_df)

    assert num_scored_rows == 2
    assert math.isclose(rmse, math.sqrt(22.5))


def test_load_actual_and_forecast_data_reads_saved_forecast_csv_for_requested_split(tmp_path) -> None:
    split_dir = tmp_path / "splits"
    forecast_dir = tmp_path / "forecasts"
    sku = SKU("FOODS_3_080", "CA_1")

    split_output_dir = split_dir / "m5_foods_3_080_ca_1"
    split_output_dir.mkdir(parents=True)
    pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02"],
            "demand": [3.0, 5.0],
        }
    ).to_csv(split_output_dir / "train.csv", index=False)
    pd.DataFrame(
        {
            "date": ["2024-01-03", "2024-01-04"],
            "demand": [7.0, 9.0],
        }
    ).to_csv(split_output_dir / "validation.csv", index=False)
    pd.DataFrame(
        {
            "date": ["2024-01-05", "2024-01-06"],
            "demand": [11.0, 13.0],
        }
    ).to_csv(split_output_dir / "test.csv", index=False)

    output_path = build_forecast_csv_path(
        output_dir=forecast_dir,
        sku=sku,
        forecast_name="naive_last_value",
        split=DataSplit.VAL,
    )
    save_forecasts(
        pd.DataFrame(
            {
                "forecast_origin_date": ["2024-01-03", "2024-01-04"],
                "target_date": ["2024-01-03", "2024-01-04"],
                "horizon_day": [1, 1],
                "predicted_demand": [6.0, 8.0],
            }
        ),
        output_path,
    )

    actual_df, forecast_df = load_actual_and_forecast_data(
        sku=sku,
        split=DataSplit.VAL,
        split_dir=split_dir,
        forecast_dir=forecast_dir,
        forecast_name="naive_last_value",
    )
    rmse, num_scored_rows = compute_rmse(actual_df, forecast_df)

    assert math.isclose(rmse, 1.0)
    assert num_scored_rows == 2
