# Data Ingestion Pipeline
## Dataset
- **Source**
The data is from the M5 Forecasting Kaggle competition [github link](https://github.com/Mcompetitions/M5-methods). 
- **Time Range**
- Daily sales history from 2011-01-29 to 2016-04-24 in `sales_train_validation.csv`.
- **Demand Granularity**
- Daily observed unit sales at the `store x item` level.
- **Number of SKUs**
- For this project, a single SKU in M5 is treated as one `item_id` in one `store_id`, since each row is store-specific.
- **Relevant Columns/Values**
- `item_id`, `dept_id`, `cat_id`, `store_id`, `state_id`, daily demand columns `d_1` through `d_1913`
- Optional covariates for later forecasting work: calendar effects from `calendar.csv` and weekly prices from `sell_prices.csv`
- **Known Limitations**
- The dataset contains observed sales, not true latent demand, so stockouts may censor demand and make some periods appear artificially low.
- The dataset does not provide explicit inventory levels or stockout flags, so the simulator must assume its own lead time, safety stock, holding cost, and stockout penalty.
- Prices are available only at weekly granularity and promotions/calendar effects are better treated as optional forecasting covariates than MVP simulator inputs.

## Pipeline
- **Loading**
- **Schema Validation**
- **Missing-period Handling**
- **Duplicate Handling**
- **Demand Aggregation**
- **Train, Validation, and Test Splits**
- **Leakage Prevention**

## Exploratory Data Analysis
- **Demand Distributions**
- **Trend and Seasonality**
- **Zero-demand Periods**
- **Demand Variability**
- **SKU Selection or Segmentation**
- **MVP SKU**
`FOODS_3_080` at store `CA_1` is used as the MVP series. It has a full history, very few zero-sales days, and moderate daily volume, making it a clean single-SKU starting point for forecasting and inventory simulation.
- **Stretch SKUs**
`FOODS_3_282` at `CA_3` is considered as an intermittent-demand stretch SKU because it has many zero-sales days and is useful for testing sparse-demand behavior.
`HOUSEHOLD_1_474` at `TX_2` is used as a spikier stretch SKU because it has larger demand spikes and offers a contrasting demand pattern outside the main food example.
