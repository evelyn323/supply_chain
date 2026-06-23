from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.types import SKU, SplitData


def load_splits(dir: str | Path, sku: SKU) -> SplitData:
    """
    Load saved train, validation, and test splits for a processed SKU series.
    """
    split_dir = Path(dir) / f"m5_{sku.item_id.lower()}_{sku.store_id.lower()}"
    return SplitData(
        train=pd.read_csv(split_dir / "train.csv"),
        val=pd.read_csv(split_dir / "validation.csv"),
        test=pd.read_csv(split_dir / "test.csv"),
    )
