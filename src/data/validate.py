import pandas as pd
from pandas.api.types import is_datetime64_any_dtype
from src.data.types import RawData

def validate_calendar(df: pd.DataFrame) -> None:
    # Check columns
    required_cols = {
        "date",
        "wm_yr_wk",
        "weekday",
        "wday",
        "month",
        "year",
        "event_name_1",
        "event_type_1",
        "event_name_2",
        "event_type_2",
        "snap_CA",
        "snap_TX",
        "snap_WI",
    }
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Calendar missing columns: {sorted(missing)}")
    
    # Date types
    if not is_datetime64_any_dtype(df["date"]):
        raise TypeError("Incorrect date object type")
    
    # Unique dates
    if not df["date"].is_unique:
        raise ValueError("Dates not unique")
    
    # Continuous dates
    sorted_df = df.sort_values("date").reset_index(drop=True)
    if not (sorted_df['date'].diff().dropna() == pd.Timedelta(days=1)).all():
        missing_days = sorted_df['date'][sorted_df['date'].diff() > pd.Timedelta(days=1)]
        raise ValueError(f"Dates not continuous, dates after gap are: {sorted(missing_days)}")


def validate_sales(df: pd.DataFrame) -> None:
    required_id_cols = {
        "item_id",
        "dept_id",
        "cat_id",
        "store_id",
        "state_id",
    }

    missing = required_id_cols - set(df.columns)
    if missing:
        raise ValueError(f"sales missing columns: {sorted(missing)}")

    day_cols = [c for c in df.columns if c.startswith("d_")]
    if not day_cols:
        raise ValueError("No sales day columns found")
    day_nums = []
    for col in day_cols:
        prefix, num = col.split("_")
        if prefix != "d" or not num.isdigit():
            raise ValueError(f"Invalid sales day column: {col}")
        day_nums.append(int(num))

    day_nums = sorted(day_nums)

    # check store x item is unique
    if df.duplicated(subset=["item_id", "dept_id", "cat_id", "store_id", "state_id"]).any():
        raise ValueError("Duplicate sales rows found for identifier keys")
    
    # continuous days
    expected = list(range(day_nums[0], day_nums[-1] + 1))
    if day_nums != expected:
        raise ValueError("Sales day columns are not continuous")
    
    # check numeric, non-negative, and non-null
    is_valid = pd.to_numeric(df[day_cols], errors='coerce').ge(0).fillna(False)
    if not is_valid.all().all():
        invalid_row_ids = df[~is_valid.all(axis=1)].index.tolist()
        raise ValueError(f"Invalid value in rows: {invalid_row_ids}")

def validate_prices(df: pd.DataFrame) -> None:
    required_cols = {"store_id", "item_id", "wm_yr_wk", "sell_price"}

    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"prices missing columns: {sorted(missing)}")

    # check uniqueness of store_id, item_id, wm_yr_wk
    if df.duplicated(subset=["store_id", "item_id", "wm_yr_wk"]).any():
        raise ValueError("Duplicate price rows found for identifier keys")
    
    # check sell_price numeric, non-negative, non-null
    is_valid = pd.to_numeric(df["sell_price"], errors='coerce').gt(0).fillna(False)
    if not is_valid.all():
        invalid_row_ids = df[~is_valid].index.tolist()
        raise ValueError(f"Invalid value in rows: {invalid_row_ids}")


def validate_raw_data(raw: RawData) -> None:
    validate_calendar(raw.calendar)
    validate_sales(raw.sales)
    validate_prices(raw.wk_prices)


