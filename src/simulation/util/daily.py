from __future__ import annotations

import csv
import json
from pathlib import Path

from src.simulation.types import DailyStateSnapshot, OutstandingOrder, SimulatorState


def init_snapshot_writer(
    snapshot_csv_path: Path | None,
) -> tuple[csv.DictWriter | None, object | None]:
    if snapshot_csv_path is None:
        return None, None

    snapshot_csv_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_file = snapshot_csv_path.open("w", newline="", encoding="utf-8")
    fieldnames = [
        "date",
        "on_hand_inventory",
        "outstanding_orders",
        "total_fulfilled_demand",
        "total_unmet_demand",
        "total_holding_cost",
        "total_stockout_cost",
        "total_stockout_days",
        "demand",
        "fulfilled_demand",
        "unmet_demand",
        "stockout_day",
    ]
    writer = csv.DictWriter(snapshot_file, fieldnames=fieldnames)
    writer.writeheader()
    return writer, snapshot_file


def build_daily_snapshot(
    state: SimulatorState,
    demand: float,
    fulfilled_demand: float,
    unmet_demand: float,
) -> DailyStateSnapshot:
    return DailyStateSnapshot(
        date=state.current_date,
        on_hand_inventory=state.on_hand_inventory,
        outstanding_orders=serialize_outstanding_orders(state.outstanding_orders),
        total_fulfilled_demand=state.total_fulfilled_demand,
        total_unmet_demand=state.total_unmet_demand,
        total_holding_cost=state.total_holding_cost,
        total_stockout_cost=state.total_stockout_cost,
        total_stockout_days=state.total_stockout_days,
        demand=demand,
        fulfilled_demand=fulfilled_demand,
        unmet_demand=unmet_demand,
        stockout_day=state.on_hand_inventory == 0,
    )


def serialize_outstanding_orders(outstanding_orders: list[OutstandingOrder]) -> str:
    return json.dumps(
        [
            {
                "quantity": order.quantity,
                "arrival_date": order.arrival_date.isoformat(),
            }
            for order in outstanding_orders
        ]
    )


def write_snapshot_row(
    snapshot_writer: csv.DictWriter | None,
    snapshot: DailyStateSnapshot,
) -> None:
    if snapshot_writer is None:
        return

    snapshot_writer.writerow(
        {
            "date": snapshot.date.isoformat(),
            "on_hand_inventory": snapshot.on_hand_inventory,
            "outstanding_orders": snapshot.outstanding_orders,
            "total_fulfilled_demand": snapshot.total_fulfilled_demand,
            "total_unmet_demand": snapshot.total_unmet_demand,
            "total_holding_cost": snapshot.total_holding_cost,
            "total_stockout_cost": snapshot.total_stockout_cost,
            "total_stockout_days": snapshot.total_stockout_days,
            "demand": snapshot.demand,
            "fulfilled_demand": snapshot.fulfilled_demand,
            "unmet_demand": snapshot.unmet_demand,
            "stockout_day": snapshot.stockout_day,
        }
    )
