from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.experiments.run_mvp_analysis import (
    build_command_plan,
    validate_required_forecast_artifacts,
)


def test_build_command_plan_uses_prebuilt_forecasts_and_never_builds_them() -> None:
    commands = build_command_plan()
    command_text = [" ".join(step["argv"]) for step in commands]
    step_names = [str(step["step_name"]) for step in commands]

    assert all("src.forecasting.build_forecasts" not in command for command in command_text)
    assert all("src.forecasting.train_xgboost" not in command for command in command_text)

    assert "evaluate_rmse_naive_last_value" in step_names
    assert "evaluate_rmse_moving_average_7" in step_names
    assert "evaluate_rmse_xgboost_recursive_7" in step_names
    assert "evaluate_rmse_chronos2" in step_names

    assert "simulate_baseline_forecast_driven_naive_last_value" in step_names
    assert "simulate_baseline_forecast_driven_moving_average_7" in step_names
    assert "simulate_baseline_forecast_driven_xgboost_recursive_7" in step_names
    assert "simulate_baseline_forecast_driven_chronos2" in step_names


def test_validate_required_forecast_artifacts_raises_with_missing_paths(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(FileNotFoundError, match="Missing required forecast artifacts"):
        validate_required_forecast_artifacts()
