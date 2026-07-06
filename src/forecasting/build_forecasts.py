from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.data.types import DataSplit, SKU
from src.data.util.split.load import load_splits
from src.forecasting.moving_average import build_moving_average_forecasts
from src.forecasting.naive_last_value import build_naive_last_value_forecasts
from src.forecasting.save_forecasts import build_forecast_csv_path, save_forecasts
from src.forecasting.types import ForecastOption


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build saved forecasts for one processed SKU series and split."
    )
    parser.add_argument(
        "--item-id",
        required=True,
        help="M5 item identifier, e.g. FOODS_3_080",
    )
    parser.add_argument(
        "--store-id",
        required=True,
        help="M5 store identifier, e.g. CA_1",
    )
    parser.add_argument(
        "--split-dir",
        type=Path,
        default=Path("data/splits"),
        help="Directory containing split train val test data",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/forecasts"),
        help="Directory to save forecast artifacts",
    )
    parser.add_argument(
        "--split",
        type=DataSplit,
        default=DataSplit.VAL,
        help="Whether to build train, val, or test forecasts",
    )
    parser.add_argument(
        "--forecast",
        type=ForecastOption,
        default=ForecastOption.NAIVE_LAST_VALUE,
        help="Forecast option to build",
    )
    parser.add_argument(
        "--max-horizon-days",
        type=int,
        default=30,
        help="Maximum forecast horizon in days to save for each forecast origin",
    )
    parser.add_argument(
        "--context-window-days",
        type=int,
        default=7,
        help="Trailing history window size for forecasts that use a context window",
    )
    return parser.parse_args()


def build_history_df(
    splits,
    split: DataSplit,
) -> pd.DataFrame:
    history_df = splits.get(split).iloc[0:0].copy()
    if split != DataSplit.TRAIN:
        history_df = pd.concat([history_df, splits.get(DataSplit.TRAIN)])
    if split == DataSplit.TEST:
        history_df = pd.concat([history_df, splits.get(DataSplit.VAL)])
    return history_df


def main() -> None:
    args = parse_args()
    sku = SKU(args.item_id, args.store_id)
    splits = load_splits(args.split_dir, sku)
    eval_df = splits.get(args.split)
    history_df = build_history_df(splits, args.split)

    if args.forecast is ForecastOption.NAIVE_LAST_VALUE:
        forecast_df = build_naive_last_value_forecasts(
            history_df=history_df,
            eval_df=eval_df,
            max_horizon_days=args.max_horizon_days,
        )
        forecast_name = args.forecast.value
    elif args.forecast is ForecastOption.MOVING_AVERAGE:
        forecast_df = build_moving_average_forecasts(
            history_df=history_df,
            eval_df=eval_df,
            max_horizon_days=args.max_horizon_days,
            context_window_days=args.context_window_days,
        )
        forecast_name = f"{args.forecast.value}_{args.context_window_days}"
    else:
        raise ValueError(f"Unsupported forecast option: {args.forecast}")

    output_path = build_forecast_csv_path(
        output_dir=args.output_dir,
        sku=sku,
        forecast_name=forecast_name,
        split=args.split,
    )
    save_forecasts(forecast_df, output_path)
    print(f"Saved {len(forecast_df)} forecasts to {output_path}")


if __name__ == "__main__":
    main()
