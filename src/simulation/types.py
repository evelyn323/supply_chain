from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import pandas as pd


class InitialStateOption(str, Enum):
    DUMMY = "dummy"
    PREV_DAY_DEMAND_PLUS_SAFETY_STOCK = "prev_day_demand_plus_safety_stock"


class PolicyOption(str, Enum):
    DUMMY = "dummy"
    FIXED_QUANTITY_PERIODIC_REORDER = "fixed_quantity_periodic_reorder"
    FIXED_REORDER_POINT = "fixed_reorder_point"
    FIXED_TARGET_ORDER_UP_TO = "fixed_target_order_up_to"


@dataclass
class InitialStateConfig:
    option: InitialStateOption
    history_needed: int = 0


@dataclass
class PolicyConfig:
    option: PolicyOption
    history_needed: int = 0
    overrides: dict[str, object] = field(default_factory=dict)


@dataclass
class SimulationAssumptions:
    lead_time_days: int = 5
    safety_stock: float = 40.0
    holding_cost: float = 0.10
    stockout_penalty: float = 2.00


@dataclass
class SimulationConfig:
    initial_state_config: InitialStateConfig
    policy_config: PolicyConfig
    assumptions: SimulationAssumptions


@dataclass
class SimulationMetrics:
    eval_start_date: pd.Timestamp
    eval_end_date: pd.Timestamp
    num_eval_days: int
    total_demand: float
    total_fulfilled_demand: float
    total_unmet_demand: float
    fill_rate: float
    stockout_days: int
    total_holding_cost: float
    total_stockout_cost: float
    total_cost: float
    ending_inventory: float


@dataclass
class DailyStateSnapshot:
    date: pd.Timestamp
    on_hand_inventory: float
    outstanding_orders: str
    total_fulfilled_demand: float
    total_unmet_demand: float
    total_holding_cost: float
    total_stockout_cost: float
    total_stockout_days: int
    demand: float
    fulfilled_demand: float
    unmet_demand: float
    stockout_day: bool


@dataclass
class SimulatorState:
    current_date: pd.Timestamp
    on_hand_inventory: float
    outstanding_orders: list["OutstandingOrder"] = field(default_factory=list)
    total_fulfilled_demand: float = 0.0
    total_unmet_demand: float = 0.0
    total_holding_cost: float = 0.0
    total_stockout_cost: float = 0.0
    total_stockout_days: int = 0

@dataclass
class OutstandingOrder:
    quantity: float
    arrival_date: pd.Timestamp
