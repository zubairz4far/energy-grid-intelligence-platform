from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from .data import ACTUAL, TIMESTAMP, TSO_FORECAST

FEATURES = [
    "tso_forecast",
    "load_lag_24",
    "load_lag_48",
    "load_lag_168",
    "load_mean_24_at_t_minus_24",
    "load_mean_168_at_t_minus_24",
    "tso_error_lag_24",
    "tso_error_mean_168_at_t_minus_24",
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
    "doy_sin",
    "doy_cos",
]


@dataclass(frozen=True)
class ForecastMetrics:
    mae_mw: float
    rmse_mw: float
    wape: float
    bias_mw: float
    p95_abs_error_mw: float
    underforecast_mwh: float


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    ordered = frame.sort_values(TIMESTAMP).copy().set_index(TIMESTAMP)
    actual = ordered[ACTUAL]
    tso = ordered[TSO_FORECAST]
    errors = actual - tso

    result = pd.DataFrame(index=ordered.index)
    result["target_mw"] = actual
    result["tso_forecast"] = tso
    result["load_lag_24"] = actual.shift(24)
    result["load_lag_48"] = actual.shift(48)
    result["load_lag_168"] = actual.shift(168)
    known_actual = actual.shift(24)
    result["load_mean_24_at_t_minus_24"] = known_actual.rolling(24, min_periods=24).mean()
    result["load_mean_168_at_t_minus_24"] = known_actual.rolling(168, min_periods=168).mean()
    known_error = errors.shift(24)
    result["tso_error_lag_24"] = known_error
    result["tso_error_mean_168_at_t_minus_24"] = known_error.rolling(
        168, min_periods=168
    ).mean()

    hour = result.index.hour.to_numpy(dtype=float)
    dow = result.index.dayofweek.to_numpy(dtype=float)
    doy = result.index.dayofyear.to_numpy(dtype=float)
    result["hour_sin"] = np.sin(2 * np.pi * hour / 24.0)
    result["hour_cos"] = np.cos(2 * np.pi * hour / 24.0)
    result["dow_sin"] = np.sin(2 * np.pi * dow / 7.0)
    result["dow_cos"] = np.cos(2 * np.pi * dow / 7.0)
    result["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    result["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    return result.dropna(subset=["target_mw", *FEATURES]).reset_index()


def temporal_boundaries(panel: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    end = pd.Timestamp(panel[TIMESTAMP].max())
    test_start = end - pd.Timedelta(days=60) + pd.Timedelta(hours=1)
    dev_start = test_start - pd.Timedelta(days=60)
    if (panel[TIMESTAMP] < dev_start).sum() < 24 * 120:
        raise ValueError("Not enough history before development window")
    return dev_start, test_start


def metrics(actual: np.ndarray, predicted: np.ndarray) -> ForecastMetrics:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    error = predicted - actual
    denominator = float(np.sum(np.abs(actual)))
    return ForecastMetrics(
        mae_mw=float(np.mean(np.abs(error))),
        rmse_mw=float(np.sqrt(np.mean(error**2))),
        wape=float(np.sum(np.abs(error)) / denominator),
        bias_mw=float(np.mean(error)),
        p95_abs_error_mw=float(np.quantile(np.abs(error), 0.95)),
        underforecast_mwh=float(np.sum(np.clip(actual - predicted, 0.0, None))),
    )


def fit_and_evaluate(
    panel: pd.DataFrame,
    *,
    dev_start: pd.Timestamp,
    test_start: pd.Timestamp,
    seed: int = 42,
) -> dict[str, object]:
    train = panel[panel[TIMESTAMP] < dev_start]
    dev = panel[(panel[TIMESTAMP] >= dev_start) & (panel[TIMESTAMP] < test_start)]
    test = panel[panel[TIMESTAMP] >= test_start]
    if min(len(train), len(dev), len(test)) == 0:
        raise ValueError("Temporal split produced an empty partition")

    x_train = train[FEATURES]
    y_train = train["target_mw"].to_numpy(dtype=float)
    x_dev = dev[FEATURES]
    y_dev = dev["target_mw"].to_numpy(dtype=float)
    x_test = test[FEATURES]
    y_test = test["target_mw"].to_numpy(dtype=float)

    baseline_dev = metrics(y_dev, dev["tso_forecast"].to_numpy(dtype=float))
    configs = {
        "residual_hgb_small": dict(max_leaf_nodes=15, l2_regularization=2.0),
        "residual_hgb_medium": dict(max_leaf_nodes=31, l2_regularization=4.0),
    }
    candidates: dict[str, tuple[HistGradientBoostingRegressor, ForecastMetrics]] = {}
    for name, config in configs.items():
        model = HistGradientBoostingRegressor(
            loss="squared_error",
            learning_rate=0.05,
            max_iter=260,
            min_samples_leaf=40,
            early_stopping=True,
            random_state=seed,
            **config,
        )
        model.fit(x_train, y_train)
        candidates[name] = (model, metrics(y_dev, model.predict(x_dev)))

    selected = min(candidates, key=lambda name: candidates[name][1].mae_mw)
    model = candidates[selected][0]
    baseline_test_pred = test["tso_forecast"].to_numpy(dtype=float)
    candidate_test_pred = model.predict(x_test)
    baseline_test = metrics(y_test, baseline_test_pred)
    candidate_test = metrics(y_test, candidate_test_pred)
    promote = (
        candidate_test.mae_mw <= 0.995 * baseline_test.mae_mw
        and candidate_test.p95_abs_error_mw <= baseline_test.p95_abs_error_mw
    )
    return {
        "split": {
            "train_rows": int(len(train)),
            "dev_rows": int(len(dev)),
            "test_rows": int(len(test)),
            "dev_start": pd.Timestamp(dev_start).isoformat(),
            "test_start": pd.Timestamp(test_start).isoformat(),
            "test_end": pd.Timestamp(test[TIMESTAMP].max()).isoformat(),
        },
        "selection": {
            "candidate": selected,
            "dev_metrics": {
                "entsoe_day_ahead": asdict(baseline_dev),
                **{name: asdict(value[1]) for name, value in candidates.items()},
            },
        },
        "test_metrics": {
            "entsoe_day_ahead": asdict(baseline_test),
            selected: asdict(candidate_test),
        },
        "promotion": {
            "decision": "PROMOTE" if promote else "REJECT",
            "rule": (
                "candidate MAE <= 99.5% of ENTSO-E day-ahead MAE and candidate p95 absolute "
                "error <= ENTSO-E"
            ),
        },
        "series": {
            "timestamps": test[TIMESTAMP].astype(str).tolist(),
            "actual": y_test.tolist(),
            "baseline": baseline_test_pred.tolist(),
            "candidate": candidate_test_pred.tolist(),
        },
        "dev_series": {
            "actual": y_dev.tolist(),
            "baseline": dev["tso_forecast"].to_numpy(dtype=float).tolist(),
            "candidate": model.predict(x_dev).tolist(),
        },
        "train_actual": train["target_mw"].to_numpy(dtype=float).tolist(),
    }
