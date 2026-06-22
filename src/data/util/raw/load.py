import pandas as pd
from pathlib import Path
from src.data.types import RawData

def load_raw(dir: str | Path) -> RawData:
    """
    Load the raw data from the directory into pandas dataframe
    """
    raw_dir = Path(dir)
    calendar = pd.read_csv(raw_dir / "calendar.csv", parse_dates=["date"])
    sales = pd.read_csv(raw_dir / "sales_train_validation.csv")
    wk_prices = pd.read_csv(raw_dir / "sell_prices.csv")
    return RawData(
        calendar,
        sales,
        wk_prices
    )
