from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import pandas as pd


class InitialStateOption(str, Enum):
    DUMMY = "dummy"


class PolicyOption(str, Enum):
    DUMMY = "dummy"


@dataclass
class InitialStateConfig:
    option: InitialStateOption
    history_needed: int = 0


@dataclass
class PolicyConfig:
    option: PolicyOption
    history_needed: int = 0


@dataclass
class SimulationConfig:
    initial_state_config: InitialStateConfig
    policy_config: PolicyConfig


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
