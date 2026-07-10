from __future__ import annotations

import argparse
from pathlib import Path

from src.data.types import SKU
from src.data.util.split.load import load_splits
from src.forecasting.xgboost_recursive import (
    build_xgboost_model_path,
    train_and_save_xgboost_model,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train and save a recursive one-step XGBoost demand model for one SKU."
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
        "--model-dir",
        type=Path,
        default=Path("data/models"),
        help="Directory to save trained XGBoost models",
    )
    parser.add_argument(
        "--context-window-days",
        type=int,
        default=7,
        help="Trailing history window size for rolling features",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sku = SKU(args.item_id, args.store_id)
    splits = load_splits(args.split_dir, sku)
    model_path = build_xgboost_model_path(
        model_dir=args.model_dir,
        sku=sku,
        context_window_days=args.context_window_days,
    )
    _, feature_columns = train_and_save_xgboost_model(
        train_df=splits.train,
        val_df=splits.val,
        context_window_days=args.context_window_days,
        model_path=model_path,
    )
    print(f"Saved XGBoost model to {model_path}")
    print(f"Feature columns: {', '.join(feature_columns)}")


if __name__ == "__main__":
    main()
