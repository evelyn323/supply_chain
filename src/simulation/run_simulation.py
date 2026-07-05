from __future__ import annotations

import argparse
import json
import pandas as pd
from pathlib import Path

from src.data.types import SKU, DataSplit
from src.data.util.split.load import load_splits
from src.simulation.initial_state_configs import get_initial_state_config
from src.simulation.initial_state import init_simulator_state
from src.simulation.policy_configs import get_policy_config
from src.simulation.policy import decide_replenishment
from src.simulation.util.history import get_available_history
from src.simulation.util.aggregate import (
    aggregate_final_metrics,
    print_final_metrics,
)
from src.simulation.util.daily import (
    build_daily_snapshot,
    init_snapshot_writer,
    write_snapshot_row,
)
from src.simulation.util.paths import build_snapshot_csv_path
from src.simulation.types import (
    InitialStateOption,
    OutstandingOrder,
    PolicyOption,
    SimulationConfig,
    SimulationAssumptions,
    SimulationMetrics,
    SimulatorState,
)


def run_simulation(
        history_df: pd.DataFrame,
        eval_df: pd.DataFrame,
        config: SimulationConfig,
        snapshot_csv_path: Path | None = None,
) -> SimulationMetrics:
    required_history = get_required_history(config)

    # sort/cleanup the demand series / chosen split
    eval_df = eval_df.copy()
    history_df = history_df.copy()
    eval_df["date"] = pd.to_datetime(eval_df["date"])
    history_df["date"] = pd.to_datetime(history_df["date"])
    eval_df = eval_df.sort_values(by="date", ascending=True)
    history_df = history_df.sort_values(by="date", ascending=True)
    requested_eval_start = eval_df.iloc[0]["date"]
    requested_eval_end = eval_df.iloc[-1]["date"]
    history_df, eval_df = get_eligible_history_and_eval(
        history_df,
        eval_df,
        required_history,
    )

    if eval_df.empty:
        raise ValueError("No eligible evaluation dates found for the requested history")

    print(
        "Required history:",
        required_history,
        "| requested eval window:",
        requested_eval_start,
        "to",
        requested_eval_end,
        "| eligible eval window:",
        eval_df.iloc[0]["date"],
        "to",
        eval_df.iloc[-1]["date"],
    )

    # initialize simulator state at first eval_date
    state = init_simulator_state(history_df, eval_df, config)
    snapshot_writer, snapshot_file = init_snapshot_writer(snapshot_csv_path)

    # start simulation loop
    try:
        for row in eval_df.itertuples(index=False):
            state.current_date = row.date
            # receive scheduled orders and update on hand inventory
            receive_scheduled_orders(state)
            # observe available information/current state
            available_history = get_available_history(history_df, eval_df, state.current_date)
            # make replenishment decision
            # TODO: Replace the dummy replenishment decision with the selected policy logic.
            order_qty = decide_replenishment(available_history, state, config)
            # schedule any new replenishment order
            schedule_replenishment(state, order_qty, config)
            # realize true demand
            fulfilled_demand, unmet_demand = realize_demand(state, row.demand)
            # record/update fulfilled and unmet demand and ending inventory
            state.total_fulfilled_demand += fulfilled_demand
            state.total_unmet_demand += unmet_demand
            if state.on_hand_inventory == 0:
                state.total_stockout_days += 1
            # compute costs from ending state
            update_daily_costs(state, unmet_demand, config)
            snapshot = build_daily_snapshot(
                state,
                demand=row.demand,
                fulfilled_demand=fulfilled_demand,
                unmet_demand=unmet_demand,
            )
            write_snapshot_row(snapshot_writer, snapshot)
    finally:
        if snapshot_file is not None:
            snapshot_file.close()

    metrics = aggregate_final_metrics(state, eval_df)
    print_final_metrics(metrics)
    return metrics


def receive_scheduled_orders(state: SimulatorState) -> None:
    remaining_orders = []
    for order in state.outstanding_orders:
        if order.arrival_date <= state.current_date:
            state.on_hand_inventory += order.quantity
        else:
            remaining_orders.append(order)
    state.outstanding_orders = remaining_orders


def schedule_replenishment(
    state: SimulatorState,
    order_quantity: float,
    config: SimulationConfig,
) -> None:
    if order_quantity <= 0:
        return

    # TODO: Decide whether order quantities should be rounded/cast to integers.
    state.outstanding_orders.append(
        OutstandingOrder(
            quantity=order_quantity,
            arrival_date=state.current_date + pd.Timedelta(days=config.assumptions.lead_time_days),
        )
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
    config: SimulationConfig,
) -> None:
    state.total_holding_cost += state.on_hand_inventory * config.assumptions.holding_cost
    state.total_stockout_cost += unmet_demand * config.assumptions.stockout_penalty


def get_required_history(config: SimulationConfig) -> int:
    return max(
        config.initial_state_config.history_needed,
        config.policy_config.history_needed,
    )


def get_eligible_history_and_eval(
    history_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    required_history: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Shift the simulated eval window forward until enough prior history is available for both initialization and the selected policy.
    """
    if required_history <= 0:
        return history_df, eval_df

    for idx, row in eval_df.iterrows():
        current_date = row["date"]
        available_history = get_available_history(history_df, eval_df, current_date)
        if len(available_history) >= required_history:
            eligible_history_df = available_history
            eligible_eval_df = eval_df.loc[idx:].copy()
            return eligible_history_df, eligible_eval_df

    return history_df, eval_df.iloc[0:0].copy()


def parse_json_object_arg(raw_value: str) -> dict[str, object]:
    try:
        parsed_value = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"Invalid JSON for policy config: {exc}") from exc

    if not isinstance(parsed_value, dict):
        raise argparse.ArgumentTypeError("Policy config must be a JSON object")

    return parsed_value


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
        "--output-dir",
        type=Path,
        default=Path("data/simulation"),
        help="Directory to save daily simulation snapshots",
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
        default=InitialStateOption.PREV_DAY_DEMAND_PLUS_SAFETY_STOCK,
        help="Initial-state option to use",
    )
    parser.add_argument(
        "--policy",
        type=PolicyOption,
        default=PolicyOption.FIXED_QUANTITY_PERIODIC_REORDER,
        help="Replenishment policy option to use",
    )
    parser.add_argument(
        "--policy-config-json",
        type=parse_json_object_arg,
        default=None,
        help="Optional JSON object with policy-specific config overrides",
    )
    parser.add_argument(
        "--lead-time-days",
        type=int,
        default=5,
        help="Fixed replenishment lead time in days",
    )
    parser.add_argument(
        "--holding-cost",
        type=float,
        default=0.10,
        help="Holding cost per unit per day",
    )
    parser.add_argument(
        "--safety-stock",
        type=float,
        default=40.0,
        help="Safety stock used by policies and initial-state rules that need it",
    )
    parser.add_argument(
        "--stockout-penalty",
        type=float,
        default=2.00,
        help="Penalty per unmet unit of demand",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sku = SKU(args.item_id, args.store_id)
    config = SimulationConfig(
        initial_state_config=get_initial_state_config(args.initial_state),
        policy_config=get_policy_config(args.policy, overrides=args.policy_config_json),
        assumptions=SimulationAssumptions(
            lead_time_days=args.lead_time_days,
            safety_stock=args.safety_stock,
            holding_cost=args.holding_cost,
            stockout_penalty=args.stockout_penalty,
        ),
    )
    splits = load_splits(args.split_dir, sku)
    eval_df = splits.get(args.split)

    history_df = eval_df.iloc[0:0].copy()
    if args.split != DataSplit.TRAIN:
        history_df = pd.concat([history_df, splits.get(DataSplit.TRAIN)])
    if args.split == DataSplit.TEST:
        history_df = pd.concat([history_df, splits.get(DataSplit.VAL)])

    snapshot_csv_path = build_snapshot_csv_path(
        args.output_dir,
        sku,
        config.policy_config,
        config.assumptions,
        args.split,
    )
    run_simulation(history_df, eval_df, config, snapshot_csv_path=snapshot_csv_path)



if __name__ == "__main__":
    main()
