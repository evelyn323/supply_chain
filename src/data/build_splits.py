from __future__ import annotations

import argparse
from pathlib import Path

from src.data.types import SKU
from src.data.util.processed.load import load_processed
from src.data.util.split.prepare import prepare_splits


def build_splits(
    item_id: str,
    store_id: str,
    processed_dir: Path,
    output_dir: Path,
    val_frac: float | None = None,
    test_frac: float | None = None,
) -> None:
    sku = SKU(item_id=item_id, store_id=store_id)
    processed_df = load_processed(processed_dir, sku)
    split_kwargs = {}
    if val_frac is not None:
        split_kwargs["val_frac"] = val_frac
    if test_frac is not None:
        split_kwargs["test_frac"] = test_frac

    split_dfs = prepare_splits(processed_df, **split_kwargs)

    sku_output_dir = output_dir / f"m5_{item_id.lower()}_{store_id.lower()}"
    sku_output_dir.mkdir(parents=True, exist_ok=True)

    split_dfs.train.to_csv(sku_output_dir / "train.csv", index=False)
    split_dfs.val.to_csv(sku_output_dir / "validation.csv", index=False)
    split_dfs.test.to_csv(sku_output_dir / "test.csv", index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build saved train, validation, and test splits for one processed SKU series."
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
        "--val-frac",
        type=float,
        help="Fraction of data for validation split"
    )
    parser.add_argument(
        "--test-frac",
        type=float,
        help="Fraction of data for test split"
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory containing processed daily series",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/splits"),
        help="Directory to save split datasets",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    build_splits(
        item_id=args.item_id,
        store_id=args.store_id,
        processed_dir=args.processed_dir,
        output_dir=args.output_dir,
        val_frac=args.val_frac,
        test_frac=args.test_frac,
    )


if __name__ == "__main__":
    main()
