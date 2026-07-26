from __future__ import annotations

import csv
import json
import shlex
import subprocess
import sys
from pathlib import Path

PYTHON_BIN = sys.executable
ITEM_ID = "FOODS_3_080"
STORE_ID = "CA_1"
SPLIT = "val"
ANALYSIS_NAME = "docs_mvp"
ANALYSIS_DIR = Path("data/analysis")

FORECAST_METHODS = [("naive_last_value", None), ("moving_average", 7)]
SENSITIVITY_SCENARIOS = [
    ("baseline", {"lead_time_days": 5, "safety_stock": 40.0, "holding_cost": 0.10, "stockout_penalty": 2.00}),
    ("lead_time_3", {"lead_time_days": 3, "safety_stock": 40.0, "holding_cost": 0.10, "stockout_penalty": 2.00}),
    ("lead_time_7", {"lead_time_days": 7, "safety_stock": 40.0, "holding_cost": 0.10, "stockout_penalty": 2.00}),
    ("safety_stock_20", {"lead_time_days": 5, "safety_stock": 20.0, "holding_cost": 0.10, "stockout_penalty": 2.00}),
    ("safety_stock_60", {"lead_time_days": 5, "safety_stock": 60.0, "holding_cost": 0.10, "stockout_penalty": 2.00}),
    ("holding_cost_0_05", {"lead_time_days": 5, "safety_stock": 40.0, "holding_cost": 0.05, "stockout_penalty": 2.00}),
    ("holding_cost_0_20", {"lead_time_days": 5, "safety_stock": 40.0, "holding_cost": 0.20, "stockout_penalty": 2.00}),
    ("stockout_penalty_1", {"lead_time_days": 5, "safety_stock": 40.0, "holding_cost": 0.10, "stockout_penalty": 1.0}),
    ("stockout_penalty_5", {"lead_time_days": 5, "safety_stock": 40.0, "holding_cost": 0.10, "stockout_penalty": 5.0}),
]
BASELINE_POLICIES = ["fixed_quantity_periodic_reorder", "fixed_reorder_point", "fixed_target_order_up_to"]


def build_forecast_name(forecast: str, context_window_days: int | None) -> str:
    if context_window_days is None:
        return forecast
    return f"{forecast}_{context_window_days}"


def build_forecast_csv_path(forecast_name: str) -> str:
    return (
        f"data/forecasts/m5_{ITEM_ID.lower()}_{STORE_ID.lower()}/"
        f"{forecast_name}/default/{SPLIT}_forecasts.csv"
    )


def build_command_plan() -> list[dict[str, object]]:
    commands: list[dict[str, object]] = []

    for forecast, context_window_days in FORECAST_METHODS:
        step_name = build_forecast_name(forecast, context_window_days)
        command = [
            PYTHON_BIN,
            "-m",
            "src.forecasting.build_forecasts",
            "--item-id",
            ITEM_ID,
            "--store-id",
            STORE_ID,
            "--split",
            SPLIT,
            "--forecast",
            forecast,
        ]
        if context_window_days is not None:
            command.extend(["--context-window-days", str(context_window_days)])
        commands.append(
            {
                "step_name": f"build_forecast_{step_name}",
                "argv": command,
            }
        )

    for forecast, context_window_days in FORECAST_METHODS:
        forecast_name = build_forecast_name(forecast, context_window_days)
        command = [
            PYTHON_BIN,
            "-m",
            "src.forecasting.evaluate_forecasts",
            "--item-id",
            ITEM_ID,
            "--store-id",
            STORE_ID,
            "--split",
            SPLIT,
            "--forecast-name",
            forecast_name,
        ]
        commands.append(
            {
                "step_name": f"evaluate_rmse_{forecast_name}",
                "argv": command,
            }
        )

    for scenario_name, scenario_args in SENSITIVITY_SCENARIOS:
        for policy in BASELINE_POLICIES:
            command = build_simulation_command(
                policy=policy,
                scenario_args=scenario_args,
                policy_config_json=None,
            )
            commands.append(
                {
                    "step_name": f"simulate_{scenario_name}_{policy}",
                    "argv": command,
                }
            )

        for forecast, context_window_days in FORECAST_METHODS:
            forecast_name = build_forecast_name(forecast, context_window_days)
            policy_config_json = json.dumps(
                {
                    "forecast_driven_order_up_to": {
                        "forecast_name": forecast_name,
                        "forecast_csv_path": build_forecast_csv_path(forecast_name),
                        "context_window_days": context_window_days or 7,
                    }
                }
            )
            command = build_simulation_command(
                policy="forecast_driven_order_up_to",
                scenario_args=scenario_args,
                policy_config_json=policy_config_json,
            )
            commands.append(
                {
                    "step_name": f"simulate_{scenario_name}_forecast_driven_{forecast_name}",
                    "argv": command,
                }
            )

    return commands


def build_simulation_command(
    *,
    policy: str,
    scenario_args: dict[str, float | int],
    policy_config_json: str | None,
) -> list[str]:
    command = [
        PYTHON_BIN,
        "-m",
        "src.simulation.run_simulation",
        "--item-id",
        ITEM_ID,
        "--store-id",
        STORE_ID,
        "--split",
        SPLIT,
        "--policy",
        policy,
        "--lead-time-days",
        str(scenario_args["lead_time_days"]),
        "--safety-stock",
        str(scenario_args["safety_stock"]),
        "--holding-cost",
        str(scenario_args["holding_cost"]),
        "--stockout-penalty",
        str(scenario_args["stockout_penalty"]),
    ]
    if policy_config_json is not None:
        command.extend(["--policy-config-json", policy_config_json])
    return command


def run_command(command: list[str], workdir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=workdir,
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> None:
    workdir = Path.cwd()
    output_dir = ANALYSIS_DIR / f"m5_{ITEM_ID.lower()}_{STORE_ID.lower()}" / ANALYSIS_NAME / SPLIT
    logs_dir = output_dir / "command_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    manifest_rows: list[dict[str, str]] = []
    for index, step in enumerate(build_command_plan(), start=1):
        log_path = logs_dir / f"{index:02d}_{step['step_name']}.log"
        print(f"[{index}] {step['step_name']}")
        argv = step["argv"]
        if not isinstance(argv, list):
            raise ValueError("Expected command argv list")
        result = run_command(argv, workdir)
        log_path.write_text(result.stdout + result.stderr)
        manifest_rows.append(
            {
                "step_name": str(step["step_name"]),
                "command": shlex.join(argv),
                "log_path": str(log_path),
            }
        )

    manifest_path = output_dir / "commands_run.csv"
    with manifest_path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["step_name", "command", "log_path"])
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(f"Saved command manifest to {manifest_path}")
    print(f"Saved command logs to {logs_dir}")


if __name__ == "__main__":
    main()
