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
- Some SKU appear to enter the assortment partway through the dataset, with long early zero-sales periods and missing early price history. These patterns may reflect product introduction timing rather than true intermittent demand.

## Pipeline Structure
- **Raw inputs**
  - Raw M5 files are loaded from `data/raw/` through `src/data/util/raw/load.py`.
- **Validation**
  - `src/data/util/raw/validate.py` checks expected columns, date continuity, sales-day continuity, uniqueness, and basic value constraints before downstream processing.
- **Processed series construction**
  - `src/data/util/processed/prepare.py` filters the selected `store x item` series, reshapes wide daily sales columns into long daily format, and merges calendar and weekly price data.
  - The processed daily series is sorted by `date` and treated as the canonical input for downstream forecasting and simulation.
- **Processed outputs**
  - `src/data/build_processed.py` orchestrates raw loading, validation, processing, and saving.
  - The build step generates a processed daily series for a selected `store x item` SKU and saves it under `data/processed/`.
  - `src/data/util/processed/load.py` loads saved processed daily series from `data/processed/`.
- **Train, validation, and test splits**
  - `src/data/util/split/` contains chronological split logic built on top of the processed daily series rather than the raw files.
  - `src/data/build_splits.py` saves `train.csv`, `validation.csv`, and `test.csv`, with default split fractions defined in `src/data/util/split/prepare.py` and optional CLI overrides.
- **Leakage prevention**
  - Feature construction and evaluation use only information available up to each forecast origin or simulation day.
- Exploratory notebooks are used for inspection only, while the main data-preparation logic resides in reproducible Python code.


## Exploratory Data Analysis
- **Demand Distributions**
- Daily demand is analyzed at the `store x item` level after reshaping M5 sales into long format.
- `FOODS_3_080` at `CA_1` has moderate daily demand and very few zero-sales days, while the other two selected SKUs provide more intermittent or spiky comparison cases.
- **Trend and Seasonality**
- Daily line plots are used to inspect broad movement over time and visible short-cycle variation in each selected series.
- Calendar fields and weekly prices are merged into the daily series so that seasonality, event effects, and price-based extensions remain available for later forecasting work.

- **SKU Selection or Segmentation**
- SKU selection emphasizes full-history availability, continuity of activity, and contrasting demand patterns.
- Late-introduction series with long leading zero stretches are treated carefully because they may reflect assortment timing rather than true intermittent demand.
- **Selected SKUs**
`FOODS_3_080` at store `CA_1` has a full history, very few zero-sales days, and moderate daily volume, making it the smoother comparison series.
`FOODS_3_234` at `WI_2` is included as an intermittent-demand SKU because it has a substantially higher share of zero-sales days than `FOODS_3_080`.
`HOUSEHOLD_1_474` at `TX_2` is included as a spikier SKU because it has larger demand spikes and offers a contrasting demand pattern outside the main food example.
