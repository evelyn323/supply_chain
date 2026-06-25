from __future__ import annotations

import pandas as pd
from dataclasses import dataclass, field

@dataclass
class SimulationConfig:
    pass


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
