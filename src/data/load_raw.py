import pandas as pd
from pathlib import Path
from src.data.types import RawData

def load_raw_data(dir: str | Path) -> RawData:
    """
    Load the raw data from the directory into pandas dataframe
    """
    calendar = pd.read_csv("../data/raw/calendar.csv", parse_dates=["date"])
    sales = pd.read_csv("../data/raw/sales_train_validation.csv")
    wk_prices = pd.read_csv("../data/raw/sell_prices.csv")
    return {
        calendar,
        sales,
        wk_prices
    }
