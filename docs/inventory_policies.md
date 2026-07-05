# Inventory Policies
## Naive Baseline
Use a fixed-quantity periodic reorder policy as a simple non-forecast benchmark. Place the same order quantity every fixed review interval.
## Fixed Reorder-Point Policy
Place a replenishment order when inventory position falls below a fixed reorder point.
Order a fixed replenishment quantity each time the threshold is crossed.
Safety stock is treated as a fixed parameter.
## Order-Up-To Policy
Order enough units to raise inventory position to a fixed target level chosen in advance.
In the current simulator, the effective target is base target plus safety stock.
## Forecast-Driven Order-Up-To Policy
Order enough units to raise inventory position to a target informed by forecasted lead-time demand plus safety stock.
The simulator reads forecast rows from a saved forecast artifact keyed by forecast origin date and target date range.
## Policy Parameters
- Fixed order quantity
- Review interval
- Reorder point
- Order-up-to level
- Forecast artifact path
- Safety stock
- Lead time
