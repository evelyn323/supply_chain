from __future__ import annotations

import pandas as pd


def get_available_history(
    history_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    current_date: pd.Timestamp,
) -> pd.DataFrame:
    prior_eval_df = eval_df[eval_df["date"] < current_date]
    return pd.concat([history_df, prior_eval_df], ignore_index=True).sort_values(
        by="date",
        ascending=True,
    )
