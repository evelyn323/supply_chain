from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from src.data.types import SKU
from src.simulation.util.history import get_available_history

LAG_DAYS: tuple[int, ...] = (1, 7, 14, 28)
DEFAULT_RANDOM_STATE = 42
DEFAULT_EARLY_STOPPING_ROUNDS = 20


def _get_xgb_regressor_class():
    try:
        from xgboost import XGBRegressor
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "xgboost is required for xgboost_recursive forecasting. "
            "Install the project environment from environment.yml first."
        ) from exc
    return XGBRegressor


def get_xgboost_forecast_name(context_window_days: int) -> str:
    return f"xgboost_recursive_{context_window_days}"


def build_xgboost_model_path(
    model_dir: Path,
    sku: SKU,
    context_window_days: int,
) -> Path:
    forecast_name = get_xgboost_forecast_name(context_window_days)
    return (
        model_dir
        / f"m5_{sku.item_id.lower()}_{sku.store_id.lower()}"
        / forecast_name
        / "default"
        / "model.json"
    )


def build_xgboost_metadata_path(
    model_path: Path,
) -> Path:
    return model_path.with_name("metadata.json")


def _normalize_history(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized["date"] = pd.to_datetime(normalized["date"])
    normalized = normalized.sort_values(by="date", ascending=True).reset_index(drop=True)
    return normalized


def _get_feature_columns(context_window_days: int, lag_days: Sequence[int]) -> list[str]:
    lag_columns = [f"lag_{lag_day}" for lag_day in lag_days]
    return [
        *lag_columns,
        f"rolling_mean_{context_window_days}",
        "day_of_week",
        "month",
        "year",
    ]


def _get_required_history(context_window_days: int, lag_days: Sequence[int]) -> int:
    return max(context_window_days, max(lag_days))


def _build_supervised_frame(
    observed_df: pd.DataFrame,
    context_window_days: int,
    lag_days: Sequence[int] = LAG_DAYS,
) -> tuple[pd.DataFrame, list[str]]:
    supervised_df = _normalize_history(observed_df)[["date", "demand"]].copy()
    for lag_day in lag_days:
        supervised_df[f"lag_{lag_day}"] = supervised_df["demand"].shift(lag_day)

    rolling_column = f"rolling_mean_{context_window_days}"
    supervised_df[rolling_column] = (
        supervised_df["demand"].shift(1).rolling(context_window_days).mean()
    )
    supervised_df["day_of_week"] = supervised_df["date"].dt.dayofweek
    supervised_df["month"] = supervised_df["date"].dt.month
    supervised_df["year"] = supervised_df["date"].dt.year

    feature_columns = _get_feature_columns(context_window_days, lag_days)
    supervised_df = supervised_df.dropna(subset=[*feature_columns, "demand"]).reset_index(drop=True)
    return supervised_df, feature_columns


def _build_split_supervised_frame(
    history_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    context_window_days: int,
) -> tuple[pd.DataFrame, list[str]]:
    history_df = _normalize_history(history_df)
    eval_df = _normalize_history(eval_df)
    combined_df = pd.concat([history_df, eval_df], ignore_index=True)
    supervised_df, feature_columns = _build_supervised_frame(
        observed_df=combined_df,
        context_window_days=context_window_days,
    )
    eval_dates = set(eval_df["date"])
    split_supervised_df = supervised_df[supervised_df["date"].isin(eval_dates)].reset_index(drop=True)
    return split_supervised_df, feature_columns


def _build_recursive_feature_row(
    observed_df: pd.DataFrame,
    target_date: pd.Timestamp,
    context_window_days: int,
    lag_days: Sequence[int] = LAG_DAYS,
) -> pd.DataFrame | None:
    observed_df = _normalize_history(observed_df)[["date", "demand"]]
    required_history = _get_required_history(context_window_days, lag_days)
    if len(observed_df) < required_history:
        return None

    feature_row: dict[str, float | int] = {}
    for lag_day in lag_days:
        feature_row[f"lag_{lag_day}"] = float(observed_df.iloc[-lag_day]["demand"])
    feature_row[f"rolling_mean_{context_window_days}"] = float(
        observed_df["demand"].tail(context_window_days).mean()
    )
    feature_row["day_of_week"] = target_date.dayofweek
    feature_row["month"] = target_date.month
    feature_row["year"] = target_date.year
    return pd.DataFrame([feature_row])


def _fit_model_with_validation(
    model,
    train_X: pd.DataFrame,
    train_y: pd.Series,
    val_X: pd.DataFrame,
    val_y: pd.Series,
):
    try:
        model.fit(
            train_X,
            train_y,
            eval_set=[(val_X, val_y)],
            verbose=False,
        )
        return model
    except TypeError:
        # Older sklearn wrappers may not accept `verbose`.
        model.fit(
            train_X,
            train_y,
            eval_set=[(val_X, val_y)],
        )
        return model


def train_xgboost_one_step_model(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    context_window_days: int,
):
    train_supervised_df, feature_columns = _build_supervised_frame(
        observed_df=train_df,
        context_window_days=context_window_days,
    )
    if train_supervised_df.empty:
        raise ValueError(
            "Not enough training history to train xgboost_recursive with the current lag setup"
        )

    XGBRegressor = _get_xgb_regressor_class()
    model = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=DEFAULT_RANDOM_STATE,
        early_stopping_rounds=DEFAULT_EARLY_STOPPING_ROUNDS,
    )

    if val_df.empty:
        model.fit(train_supervised_df[feature_columns], train_supervised_df["demand"])
        return model, feature_columns

    val_supervised_df, _ = _build_split_supervised_frame(
        history_df=train_df,
        eval_df=val_df,
        context_window_days=context_window_days,
    )
    if val_supervised_df.empty:
        model.fit(train_supervised_df[feature_columns], train_supervised_df["demand"])
        return model, feature_columns

    model = _fit_model_with_validation(
        model=model,
        train_X=train_supervised_df[feature_columns],
        train_y=train_supervised_df["demand"],
        val_X=val_supervised_df[feature_columns],
        val_y=val_supervised_df["demand"],
    )
    return model, feature_columns


def save_xgboost_model(
    model,
    model_path: Path,
    context_window_days: int,
    feature_columns: Sequence[str],
) -> None:
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(model_path))

    metadata = {
        "context_window_days": context_window_days,
        "feature_columns": list(feature_columns),
        "lag_days": list(LAG_DAYS),
    }
    build_xgboost_metadata_path(model_path).write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )


def load_xgboost_model(model_path: Path):
    XGBRegressor = _get_xgb_regressor_class()
    model = XGBRegressor()
    model.load_model(str(model_path))
    return model


def load_xgboost_metadata(model_path: Path) -> dict[str, object]:
    metadata_path = build_xgboost_metadata_path(model_path)
    if not metadata_path.exists():
        raise FileNotFoundError(f"Missing XGBoost metadata file: {metadata_path}")
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def train_and_save_xgboost_model(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    context_window_days: int,
    model_path: Path,
) -> tuple[object, list[str]]:
    model, feature_columns = train_xgboost_one_step_model(
        train_df=train_df,
        val_df=val_df,
        context_window_days=context_window_days,
    )
    save_xgboost_model(
        model=model,
        model_path=model_path,
        context_window_days=context_window_days,
        feature_columns=feature_columns,
    )
    return model, feature_columns


def build_xgboost_recursive_forecasts(
    model,
    history_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    max_horizon_days: int,
    context_window_days: int,
) -> pd.DataFrame:
    if max_horizon_days <= 0:
        raise ValueError("max_horizon_days must be positive")
    if context_window_days <= 0:
        raise ValueError("context_window_days must be positive")

    history_df = _normalize_history(history_df)
    eval_df = _normalize_history(eval_df)

    feature_columns = _get_feature_columns(context_window_days, LAG_DAYS)
    forecast_rows: list[dict[str, object]] = []
    required_history = _get_required_history(context_window_days, LAG_DAYS)
    for row in eval_df.itertuples(index=False):
        forecast_origin_date = row.date
        available_history = get_available_history(history_df, eval_df, forecast_origin_date)
        if len(available_history) < required_history:
            continue

        recursive_history = available_history[["date", "demand"]].copy()
        for horizon_day in range(1, max_horizon_days + 1):
            target_date = forecast_origin_date + pd.Timedelta(days=horizon_day)
            feature_row = _build_recursive_feature_row(
                observed_df=recursive_history,
                target_date=target_date,
                context_window_days=context_window_days,
            )
            if feature_row is None:
                break

            predicted_demand = float(model.predict(feature_row[feature_columns])[0])
            predicted_demand = max(predicted_demand, 0.0)
            forecast_rows.append(
                {
                    "forecast_origin_date": forecast_origin_date,
                    "target_date": target_date,
                    "horizon_day": horizon_day,
                    "predicted_demand": predicted_demand,
                }
            )
            recursive_history = pd.concat(
                [
                    recursive_history,
                    pd.DataFrame(
                        {
                            "date": [target_date],
                            "demand": [predicted_demand],
                        }
                    ),
                ],
                ignore_index=True,
            )

    return pd.DataFrame(
        forecast_rows,
        columns=[
            "forecast_origin_date",
            "target_date",
            "horizon_day",
            "predicted_demand",
        ],
    )
