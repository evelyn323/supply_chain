import pandas as pd
from pathlib import Path
from src.data.types import SKU

def load_processed(dir: str | Path, sku: SKU) -> pd.DataFrame:
    """
    Load the processed data from the directory into pandas dataframe
    """
    processed_dir = Path(dir)
    df = pd.read_csv(processed_dir / f"m5_{sku.item_id.lower()}_{sku.store_id.lower()}_daily.csv")
    return df
