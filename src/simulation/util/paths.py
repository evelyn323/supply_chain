from __future__ import annotations

from pathlib import Path

from src.data.types import DataSplit, SKU
from src.simulation.types import PolicyOption, SimulationAssumptions


def build_snapshot_csv_path(
    output_dir: Path,
    sku: SKU,
    policy: PolicyOption,
    assumptions: SimulationAssumptions,
    split: DataSplit,
) -> Path:
    return (
        output_dir
        / f"m5_{sku.item_id.lower()}_{sku.store_id.lower()}"
        / policy.value
        / build_assumption_profile_slug(assumptions)
        / f"{split.value}_daily_snapshots.csv"
    )


def build_assumption_profile_slug(
    assumptions: SimulationAssumptions,
) -> str:
    default_assumptions = SimulationAssumptions()
    if assumptions == default_assumptions:
        return "default"

    return (
        f"lt_{assumptions.lead_time_days}"
        f"_ss_{format_numeric_slug(assumptions.safety_stock)}"
        f"_hc_{format_numeric_slug(assumptions.holding_cost)}"
        f"_sp_{format_numeric_slug(assumptions.stockout_penalty)}"
    )


def format_numeric_slug(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")
