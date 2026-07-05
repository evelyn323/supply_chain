from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.types import DataSplit, SKU


def build_forecast_csv_path(
    output_dir: Path,
    sku: SKU,
    forecast_name: str,
    split: DataSplit,
    config_slug: str = "default",
) -> Path:
    return (
        output_dir
        / f"m5_{sku.item_id.lower()}_{sku.store_id.lower()}"
        / forecast_name
        / config_slug
        / f"{split.value}_forecasts.csv"
    )


def save_forecasts(
    forecast_df: pd.DataFrame,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    forecast_to_save = forecast_df.copy()
    for column in ("forecast_origin_date", "target_date"):
        if column in forecast_to_save.columns:
            forecast_to_save[column] = pd.to_datetime(forecast_to_save[column])
    forecast_to_save.to_csv(output_path, index=False)
