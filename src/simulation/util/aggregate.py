from __future__ import annotations

import pandas as pd

from src.simulation.types import SimulationMetrics, SimulatorState


def aggregate_final_metrics(
    state: SimulatorState,
    eval_df: pd.DataFrame,
) -> SimulationMetrics:
    total_demand = state.total_fulfilled_demand + state.total_unmet_demand
    fill_rate = state.total_fulfilled_demand / total_demand if total_demand > 0 else 0.0
    return SimulationMetrics(
        eval_start_date=eval_df.iloc[0]["date"],
        eval_end_date=eval_df.iloc[-1]["date"],
        num_eval_days=len(eval_df),
        total_demand=total_demand,
        total_fulfilled_demand=state.total_fulfilled_demand,
        total_unmet_demand=state.total_unmet_demand,
        fill_rate=fill_rate,
        stockout_days=state.total_stockout_days,
        total_holding_cost=state.total_holding_cost,
        total_stockout_cost=state.total_stockout_cost,
        total_cost=state.total_holding_cost + state.total_stockout_cost,
        ending_inventory=state.on_hand_inventory,
    )


def print_final_metrics(metrics: SimulationMetrics) -> None:
    print("Final metrics:")
    print("  Eval window:", metrics.eval_start_date, "to", metrics.eval_end_date)
    print("  Num eval days:", metrics.num_eval_days)
    print("  Total demand:", metrics.total_demand)
    print("  Total fulfilled demand:", metrics.total_fulfilled_demand)
    print("  Total unmet demand:", metrics.total_unmet_demand)
    print("  Fill rate:", round(metrics.fill_rate, 4))
    print("  Stockout days:", metrics.stockout_days)
    print("  Total holding cost:", round(metrics.total_holding_cost, 4))
    print("  Total stockout cost:", round(metrics.total_stockout_cost, 4))
    print("  Total cost:", round(metrics.total_cost, 4))
    print("  Ending inventory:", metrics.ending_inventory)
