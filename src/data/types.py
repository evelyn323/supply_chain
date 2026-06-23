import pandas as pd
from dataclasses import dataclass

@dataclass
class RawData:
    calendar: pd.DataFrame
    sales: pd.DataFrame
    wk_prices: pd.DataFrame

@dataclass
class SplitData:
    train: pd.DataFrame
    val: pd.DataFrame
    test: pd.DataFrame

@dataclass
class SKU:
    item_id: str
    store_id: str
