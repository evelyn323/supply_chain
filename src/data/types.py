import pandas as pd
from dataclasses import dataclass
from enum import Enum

@dataclass
class RawData:
    calendar: pd.DataFrame
    sales: pd.DataFrame
    wk_prices: pd.DataFrame

class DataSplit(str, Enum):
    TRAIN = "train"
    VAL = "val"
    TEST = "test"

@dataclass
class SplitData:
    train: pd.DataFrame
    val: pd.DataFrame
    test: pd.DataFrame

    def get(self, split: DataSplit) -> pd.DataFrame:
        if split is DataSplit.TRAIN:
            return self.train
        if split is DataSplit.VAL:
            return self.val
        return self.test

@dataclass
class SKU:
    item_id: str
    store_id: str
