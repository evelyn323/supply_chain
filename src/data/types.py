import pandas as pd
from dataclasses import dataclass

@dataclass
class RawData:
    calendar: pd.DataFrame
    sales: pd.DataFrame
    wk_prices: pd.DataFrame