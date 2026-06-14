# Inventory Simulator
## Simulator Assumptions and Design

| Assumption | MVP Choice | Sensitivity Range | Notes |
| --- | --- | --- | --- |
| Time unit | 1 day | None | Matches the daily granularity of the M5 demand data. |
| Demand input | Observed daily sales | None | Treat demand as exogenous. Observed sales may censor true demand during stockouts. |
| SKU scope | One `store x item` series | Optional stretch to a small multi-SKU set | In M5, each row is store-specific. |
| Stockout model | Lost sales | None | No backorders in the MVP. |
| Lead time | 5 days | 3, 5, 7 days | Fixed within a simulation run. |
| Initial inventory | Initialize at the policy target level | None | Avoids artificial startup stockouts. |
| Safety stock | 40 units | 20, 40, 60 units | Fixed within a simulation run. |
| Holding cost | 0.10 per unit per day | 0.05, 0.10, 0.20 per unit per day | Computed using ending inventory each day. |
| Stockout penalty | 2.00 per unmet unit | 1.00, 2.00, 5.00 per unmet unit | Applied under the lost-sales assumption. |
| Price and promotion effects | Ignored in the simulator | Optional forecasting covariates later | Not explicitly modeled in the MVP simulator. |
| Omitted costs | Fixed ordering cost, unit purchasing cost, disposal or spoilage cost | None | Total cost includes holding cost and stockout penalty only. |
| Information available to policies | Current inventory state and past demand-based inputs | None | Policies do not observe future demand. |

## Simulator State
- **On-hand Inventory**
- **On-order Inventory**
- **Inventory Position**
- **Outstanding Backorders (Stretch)**
## Period Event Sequence
1. Receive scheduled orders
2. Observe available information
3. Make a replenishment decision
4. Realize demand
5. Record fulfilled and unmet demand
6. Calculate inventory and costs

## Simulator Validation
- **Hand-calculated test scenarios**
- **Invariant checks**
- **Unit Tests**
- **Edge Cases**
