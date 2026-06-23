from __future__ import annotations

import pandas as pd
from src.data.types import SplitData


def prepare_splits(processed_df: pd.DataFrame, val_frac=0.2, test_frac=0.1) -> SplitData:
    """
    Return chronological train, validation, and test splits built from a
    processed daily series.
    """
    if (val_frac < 0 or test_frac < 0 or val_frac + test_frac > 1):
        raise ValueError("Invalid validation or test fraction value")


    df = processed_df.sort_values("date").reset_index(drop=True)

    val_size = int(len(df) * val_frac)
    test_size = int(len(df) * test_frac)
    train_size = len(df) - val_size - test_size

    if train_size <= 0 or val_size <= 0 or test_size <= 0:
        raise ValueError("Split fractions must produce non-empty train, val, and test sets")

    train = df.iloc[0:train_size, :]
    val =  df.iloc[train_size:train_size + val_size, :]
    test = df.iloc[train_size + val_size:len(df), :]

    return SplitData(
        train,
        val,
        test
        )
