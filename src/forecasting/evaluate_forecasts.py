from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

from src.data.types import DataSplit, SKU
from src.data.util.split.load import load_splits
from src.forecasting.read_forecasts import load_forecasts
from src.forecasting.save_forecasts import build_forecast_csv_path


def load_actual_and_forecast_data(
    sku: SKU,
    split: DataSplit,
    split_dir: Path,
    forecast_dir: Path,
    forecast_name: str,
    config_slug: str = "default",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    splits = load_splits(split_dir, sku)
    actual_df = splits.get(split).copy()
    actual_df["date"] = pd.to_datetime(actual_df["date"])

    forecast_csv_path = build_forecast_csv_path(
        output_dir=forecast_dir,
        sku=sku,
        forecast_name=forecast_name,
        split=split,
        config_slug=config_slug,
    )
    forecast_df = load_forecasts(str(forecast_csv_path))
    return actual_df, forecast_df


def compute_rmse(
    actual_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
) -> tuple[float, int]:
    scored_df = forecast_df.copy()
    scored_df["target_date"] = pd.to_datetime(scored_df["target_date"])
    scored_df = scored_df.merge(
        actual_df[["date", "demand"]],
        how="inner",
        left_on="target_date",
        right_on="date",
    )

    if scored_df.empty:
        raise ValueError("No forecast rows matched actual demand dates for RMSE scoring")

    squared_errors = (scored_df["predicted_demand"] - scored_df["demand"]) ** 2
    rmse = math.sqrt(float(squared_errors.mean()))
    return rmse, len(scored_df)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute RMSE for one saved forecast artifact against one SKU split."
    )
    parser.add_argument("--item-id", required=True, help="M5 item identifier, e.g. FOODS_3_080")
    parser.add_argument("--store-id", required=True, help="M5 store identifier, e.g. CA_1")
    parser.add_argument(
        "--split-dir",
        type=Path,
        default=Path("data/splits"),
        help="Directory containing split train val test data",
    )
    parser.add_argument(
        "--forecast-dir",
        type=Path,
        default=Path("data/forecasts"),
        help="Directory containing saved forecast artifacts",
    )
    parser.add_argument(
        "--split",
        type=DataSplit,
        default=DataSplit.VAL,
        help="Whether to evaluate the train, val, or test forecast CSV",
    )
    parser.add_argument(
        "--forecast-name",
        required=True,
        help="Saved forecast artifact name, e.g. naive_last_value or moving_average_7",
    )
    parser.add_argument(
        "--config-slug",
        default="default",
        help="Forecast config slug inside the forecast artifact directory",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sku = SKU(args.item_id, args.store_id)
    actual_df, forecast_df = load_actual_and_forecast_data(
        sku=sku,
        split=args.split,
        split_dir=args.split_dir,
        forecast_dir=args.forecast_dir,
        forecast_name=args.forecast_name,
        config_slug=args.config_slug,
    )
    rmse, num_scored_rows = compute_rmse(actual_df, forecast_df)

    print("Forecast RMSE:")
    print("  SKU:", f"{sku.item_id} @ {sku.store_id}")
    print("  Forecast:", args.forecast_name)
    print("  Split:", args.split.value)
    print("  Eval window:", actual_df.iloc[0]["date"], "to", actual_df.iloc[-1]["date"])
    print("  Scored forecast rows:", num_scored_rows)
    print("  RMSE:", round(rmse, 4))


if __name__ == "__main__":
    main()
