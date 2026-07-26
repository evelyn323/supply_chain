from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data.types import SKU
from src.forecasting.xgboost_recursive import (
    build_xgboost_model_path,
    build_xgboost_recursive_forecasts,
    get_xgboost_forecast_name,
    load_xgboost_metadata,
    load_xgboost_model,
    train_and_save_xgboost_model,
)


class DummyXGBRegressor:
    saved_payloads: dict[str, dict[str, object]] = {}

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.loaded_from: str | None = None

    def fit(self, X: pd.DataFrame, y: pd.Series, eval_set=None, verbose=None) -> None:
        self.feature_names_ = list(X.columns)
        self.seen_targets_ = y.tolist()
        self.eval_rows_ = 0 if eval_set is None else len(eval_set[0][0])

    def predict(self, X: pd.DataFrame):
        return (X["lag_1"] + 1.0).to_numpy()

    def save_model(self, path: str) -> None:
        DummyXGBRegressor.saved_payloads[path] = {
            "kwargs": self.kwargs,
            "feature_names": getattr(self, "feature_names_", []),
            "seen_targets": getattr(self, "seen_targets_", []),
            "eval_rows": getattr(self, "eval_rows_", 0),
        }
        Path(path).write_text("dummy-model", encoding="utf-8")

    def load_model(self, path: str) -> None:
        self.loaded_from = path
        payload = DummyXGBRegressor.saved_payloads[path]
        self.kwargs = payload["kwargs"]
        self.feature_names_ = payload["feature_names"]
        self.seen_targets_ = payload["seen_targets"]
        self.eval_rows_ = payload["eval_rows"]


def test_train_and_save_xgboost_model_uses_validation_and_saves_metadata(
    monkeypatch,
    tmp_path,
) -> None:
    train_df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=40, freq="D"),
            "demand": [float(i) for i in range(1, 41)],
        }
    )
    val_df = pd.DataFrame(
        {
            "date": pd.date_range("2024-02-10", periods=5, freq="D"),
            "demand": [41.0, 42.0, 43.0, 44.0, 45.0],
        }
    )

    monkeypatch.setattr(
        "src.forecasting.xgboost_recursive._get_xgb_regressor_class",
        lambda: DummyXGBRegressor,
    )

    model_path = tmp_path / "model.json"
    model, feature_columns = train_and_save_xgboost_model(
        train_df=train_df,
        val_df=val_df,
        context_window_days=7,
        model_path=model_path,
    )

    metadata = load_xgboost_metadata(model_path)
    loaded_model = load_xgboost_model(model_path)

    assert model_path.exists()
    assert feature_columns == [
        "lag_1",
        "lag_7",
        "lag_14",
        "lag_28",
        "rolling_mean_7",
        "day_of_week",
        "month",
        "year",
    ]
    assert metadata["context_window_days"] == 7
    assert metadata["feature_columns"] == feature_columns
    assert model.eval_rows_ > 0
    assert loaded_model.loaded_from == str(model_path)


def test_build_xgboost_recursive_forecasts_rolls_predictions_forward() -> None:
    history_df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=35, freq="D"),
            "demand": [float(i) for i in range(1, 36)],
        }
    )
    eval_df = pd.DataFrame(
        {
            "date": pd.date_range("2024-02-05", periods=2, freq="D"),
            "demand": [36.0, 37.0],
        }
    )

    model = DummyXGBRegressor()
    forecast_df = build_xgboost_recursive_forecasts(
        model=model,
        history_df=history_df,
        eval_df=eval_df,
        max_horizon_days=2,
        context_window_days=7,
    )

    assert forecast_df["forecast_origin_date"].tolist() == [
        pd.Timestamp("2024-02-05"),
        pd.Timestamp("2024-02-05"),
        pd.Timestamp("2024-02-06"),
        pd.Timestamp("2024-02-06"),
    ]
    assert forecast_df["target_date"].tolist() == [
        pd.Timestamp("2024-02-05"),
        pd.Timestamp("2024-02-06"),
        pd.Timestamp("2024-02-06"),
        pd.Timestamp("2024-02-07"),
    ]
    assert forecast_df["predicted_demand"].tolist() == [36.0, 37.0, 37.0, 38.0]


def test_build_xgboost_model_path_is_deterministic() -> None:
    model_path = build_xgboost_model_path(
        model_dir=Path("data/models"),
        sku=SKU("FOODS_3_080", "CA_1"),
        context_window_days=7,
    )

    assert get_xgboost_forecast_name(7) == "xgboost_recursive_7"
    assert model_path == Path(
        "data/models/m5_foods_3_080_ca_1/xgboost_recursive_7/default/model.json"
    )
