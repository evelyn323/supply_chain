from __future__ import annotations

from pathlib import Path

from src.data.types import DataSplit, SKU
from src.simulation.policy_configs import get_policy_config
from src.simulation.types import PolicyConfig, SimulationAssumptions


def build_snapshot_csv_path(
    output_dir: Path,
    sku: SKU,
    policy_config: PolicyConfig,
    assumptions: SimulationAssumptions,
    split: DataSplit,
) -> Path:
    policy_dir = output_dir / f"m5_{sku.item_id.lower()}_{sku.store_id.lower()}" / policy_config.option.value
    policy_config_slug = build_policy_config_slug(policy_config)
    if policy_config_slug is not None:
        policy_dir = policy_dir / policy_config_slug

    return (
        policy_dir
        / build_assumption_profile_slug(assumptions)
        / f"{split.value}_daily_snapshots.csv"
    )


def build_policy_config_slug(
    policy_config: PolicyConfig,
) -> str | None:
    default_policy_config = get_policy_config(policy_config.option)
    if policy_config.overrides == default_policy_config.overrides:
        return None

    slug_parts = []
    for key in sorted(policy_config.overrides):
        if key.endswith("_path"):
            continue
        value = policy_config.overrides[key]
        slug_parts.append(f"{format_key_slug(key)}_{format_value_slug(value)}")
    if not slug_parts:
        return None
    return "_".join(slug_parts)


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


def format_key_slug(value: str) -> str:
    return value.replace("_", "-")


def format_value_slug(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int | float):
        return format_numeric_slug(float(value))
    return str(value).replace("_", "-")
