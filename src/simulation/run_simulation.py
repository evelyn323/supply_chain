from __future__ import annotations

import argparse
import pandas as pd
from pathlib import Path

from src.data.types import SKU, DataSplit
from src.data.util.split.load import load_splits
from src.simulation.initial_state_configs import get_initial_state_config
from src.simulation.initial_state import init_simulator_state
from src.simulation.policy_configs import get_policy_config
from src.simulation.policy import decide_replenishment
from src.simulation.types import (
    InitialStateOption,
    OutstandingOrder,
    PolicyOption,
    SimulationConfig,
    SimulatorState,
)


def run_simulation(
        history_df: pd.DataFrame,
        eval_df: pd.DataFrame,
        config: SimulationConfig,
):
    # sort/cleanup the demand series / chosen split
    eval_df = eval_df.copy()
    history_df = history_df.copy()
    eval_df["date"] = pd.to_datetime(eval_df["date"])
    history_df["date"] = pd.to_datetime(history_df["date"])
    eval_df = eval_df.sort_values(by="date", ascending=True)
    history_df = history_df.sort_values(by="date", ascending=True)
    # TODO: Use required_history to find the first eligible evaluation date.
    required_history = get_required_history(config)
    _ = required_history

    # initialize simulator state at first eval_date
    # TODO: Replace the dummy initializer with the chosen policy-specific rule.
    state = init_simulator_state(history_df, eval_df, config)

    # start simulation loop
    for row in eval_df.itertuples(index=False):
        state.current_date = row.date
        # receive scheduled orders and update on hand inventory
        receive_scheduled_orders(state)
        # observe available information/current state
        # TODO: Decide whether policies observe full prior eval history
        available_history = get_available_history(history_df, eval_df, state.current_date)
        # make replenishment decision
        # TODO: Replace the dummy replenishment decision with the selected policy logic.
        order_qty = decide_replenishment(available_history, state, config)
        # schedule any new replenishment order
        schedule_replenishment(state, order_qty)
        # realize true demand
        fulfilled_demand, unmet_demand = realize_demand(state, row.demand)
        # record/update fulfilled and unmet demand and ending inventory
        state.total_fulfilled_demand += fulfilled_demand
        state.total_unmet_demand += unmet_demand
        if state.on_hand_inventory == 0:
            state.total_stockout_days += 1
        # compute costs from ending state
        # TODO: Apply configured holding-cost and stockout-penalty rates.
        update_daily_costs(state, unmet_demand)
        # TODO: Save daily results for debugging and final metric calculation.

    # TODO: Compute final metrics and return a simulation result object.


def receive_scheduled_orders(state: SimulatorState) -> None:
    remaining_orders = []
    for order in state.outstanding_orders:
        if order.arrival_date <= state.current_date:
            state.on_hand_inventory += order.quantity
        else:
            remaining_orders.append(order)
    state.outstanding_orders = remaining_orders


def get_available_history(
    history_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    current_date: pd.Timestamp,
) -> pd.DataFrame:
    # TODO: Confirm whether policies should see all prior eval rows
    prior_eval_df = eval_df[eval_df["date"] < current_date]
    return pd.concat([history_df, prior_eval_df], ignore_index=True)


def schedule_replenishment(
    state: SimulatorState,
    order_quantity: float,
) -> None:
    if order_quantity <= 0:
        return

    # TODO: Use configured lead time when scheduling replenishment arrivals.
    # TODO: Decide whether order quantities should be rounded/cast to integers.
    state.outstanding_orders.append(
        OutstandingOrder(quantity=order_quantity, arrival_date=state.current_date)
    )


def realize_demand(
    state: SimulatorState,
    demand: float,
) -> tuple[float, float]:
    # TODO: MVP remains lost-sales only with no backorders.
    fulfilled_demand = min(state.on_hand_inventory, demand)
    unmet_demand = max(demand - fulfilled_demand, 0.0)
    state.on_hand_inventory -= fulfilled_demand
    return fulfilled_demand, unmet_demand


def update_daily_costs(
    state: SimulatorState,
    unmet_demand: float,
) -> None:
    # TODO: use ending inventory (as stated in docs) to compute the actual cost, not just 1 cost per unit?
    state.total_holding_cost += state.on_hand_inventory
    state.total_stockout_cost += unmet_demand


def get_required_history(config: SimulationConfig) -> int:
    return max(
        config.initial_state_config.history_needed,
        config.policy_config.history_needed,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build saved train, validation, and test splits for one processed SKU series."
    )

    parser.add_argument(
        "--item-id",
        required=True,
        help="M5 item identifier, e.g. FOODS_3_080",
    )
    parser.add_argument(
        "--store-id",
        required=True,
        help="M5 store identifier, e.g. CA_1",
    )
    parser.add_argument(
        "--split-dir",
        type=Path,
        default=Path("data/splits"),
        help="Directory containing split train val test data",
    )
    parser.add_argument(
        "--split",
        type=DataSplit,
        default=DataSplit.TRAIN,
        help="Whether to use train, val, or test data",
    )
    parser.add_argument(
        "--initial-state",
        type=InitialStateOption,
        default=InitialStateOption.DUMMY,
        help="Initial-state option to use (dummy)",
    )
    parser.add_argument(
        "--policy",
        type=PolicyOption,
        default=PolicyOption.DUMMY,
        help="Replenishment policy option to use (dummy)",
    )

    return parser.parse_args()
def main() -> None:
    args = parse_args()
    sku = SKU(args.item_id, args.store_id)
    config = SimulationConfig(
        initial_state_config=get_initial_state_config(args.initial_state),
        policy_config=get_policy_config(args.policy),
    )
    splits = load_splits(args.split_dir, sku)
    eval_df = splits.get(args.split)

    history_df = eval_df.iloc[0:0].copy()
    if args.split != DataSplit.TRAIN:
        history_df = pd.concat([history_df, splits.get(DataSplit.TRAIN)])
    if args.split == DataSplit.TEST:
        history_df = pd.concat([history_df, splits.get(DataSplit.VAL)])


    run_simulation(history_df, eval_df, config)



if __name__ == "__main__":
    main()
