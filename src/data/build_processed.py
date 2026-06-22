from __future__ import annotations

import argparse
from pathlib import Path

from src.data.util.raw.load import load_raw
from src.data.util.processed.prepare import prepare_processed
from src.data.types import SKU
from src.data.util.raw.validate import validate_raw


def build_processed_dataset(
    item_id: str,
    store_id: str,
    raw_dir: Path,
    output_path: Path,
) -> None:
    sku = SKU(item_id=item_id, store_id=store_id)

    raw_data = load_raw(raw_dir)
    validate_raw(raw_data)

    sku_df = prepare_processed(raw_data, sku)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sku_df.to_csv(output_path, index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a processed daily M5 dataset for one store-item SKU."
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
        "--raw-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory containing raw M5 CSV files",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Path to save the processed dataset",
    )

    return parser.parse_args()


def main() -> None:
    """
    Builds the processed dataset for the specified SKU by:
    1. loading the raw data
    2. validating
    3. preparing the series
    4. saving processed dataset
    """
    args = parse_args()

    output_path = args.output_path
    if output_path is None:
        filename = f"m5_{args.item_id.lower()}_{args.store_id.lower()}_daily.csv"
        output_path = Path("data/processed") / filename

    build_processed_dataset(
        item_id=args.item_id,
        store_id=args.store_id,
        raw_dir=args.raw_dir,
        output_path=output_path,
    )


if __name__ == "__main__":
    main()