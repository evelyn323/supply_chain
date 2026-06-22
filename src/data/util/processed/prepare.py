import pandas as pd
from src.data.types import RawData, SKU

def prepare_processed(data: RawData, sku: SKU) -> pd.DataFrame:
    """
    Return a processed daily time-series dataframe for one M5 store-item SKU.

    The returned dataframe contains one row per day for the selected
    `store_id` and `item_id`, sorted by `date`. It includes identifier
    columns such as `item_id`, `store_id`, `dept_id`, `cat_id`, and
    `state_id`, observed daily sales in `demand`, the original M5 day key
    `d`, calendar fields merged from `calendar.csv`, and weekly prices
    merged from `sell_prices.csv` through `wm_yr_wk`.

    Price values may be missing for early periods if the SKU entered the
    store assortment partway through the dataset.
    """
    sales_df = data.sales
    wk_prices_df = data.wk_prices
    calendar_df = data.calendar
    calendar_df["d"] = [f"d_{i}" for i in range(1, len(calendar_df) + 1)]

    # convert sales from wide to long format, and merge with calendar to get dates
    sku_df = sales_df[(sales_df["store_id"] == sku.store_id) & (sales_df["item_id"] == sku.item_id)]
    sku_df = pd.melt(sku_df,
                    id_vars=["item_id", "dept_id", "cat_id", "store_id", "state_id"],
                    value_vars=[c for c in sku_df.columns if c.startswith("d_")],
                    var_name="d",
                    value_name="demand")

    sku_df = sku_df.merge(
        calendar_df,
        on="d",
        how="left",
    )
    sku_df = sku_df.sort_values("date").reset_index(drop=True)

    # merge with price of product
    price_df = wk_prices_df[
        (wk_prices_df["store_id"] == sku.store_id) &
        (wk_prices_df["item_id"] == sku.item_id)
    ].copy()

    sku_df = sku_df.merge(
        price_df,
        on=["store_id", "item_id", "wm_yr_wk"],
        how="left"
    )

    return sku_df
