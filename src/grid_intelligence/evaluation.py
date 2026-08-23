from __future__ import annotations

import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn

from .data import (
    ACTUAL,
    OPSD_DOI,
    OPSD_PACKAGE_URL,
    OPSD_VERSION,
    TIMESTAMP,
    TSO_FORECAST,
    load_grid_data,
    sha256_file,
    usable_load_rows,
)
from .forecasting import build_features, fit_and_evaluate, temporal_boundaries
from .risk import interval_metrics, ramp_metrics, reserve_metrics


def _arrays(section: dict[str, object]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return (
        np.asarray(section["actual"], dtype=float),
        np.asarray(section["baseline"], dtype=float),
        np.asarray(section["candidate"], dtype=float),
    )


def evaluate(data_dir: str | Path, *, download: bool = False, seed: int = 42) -> dict[str, object]:
    dataset = load_grid_data(data_dir, download=download)
    usable = usable_load_rows(dataset.frame)
    panel = build_features(dataset.frame)
    dev_start, test_start = temporal_boundaries(panel)
    forecast = fit_and_evaluate(panel, dev_start=dev_start, test_start=test_start, seed=seed)

    test_actual, test_baseline, test_candidate = _arrays(forecast["series"])
    dev_actual, dev_baseline, dev_candidate = _arrays(forecast["dev_series"])
    train_actual = np.asarray(forecast["train_actual"], dtype=float)

    uncertainty = {
        "entsoe_day_ahead": interval_metrics(
            dev_actual, dev_baseline, test_actual, test_baseline, coverage=0.90
        ),
        "candidate": interval_metrics(
            dev_actual, dev_candidate, test_actual, test_candidate, coverage=0.90
        ),
    }
    reserve = {
        "entsoe_day_ahead": reserve_metrics(dev_actual, dev_baseline, test_actual, test_baseline),
        "candidate": reserve_metrics(dev_actual, dev_candidate, test_actual, test_candidate),
    }
    ramps = {
        "entsoe_day_ahead": ramp_metrics(train_actual, test_actual, test_baseline),
        "candidate": ramp_metrics(train_actual, test_actual, test_candidate),
    }

    compact_forecast = {
        key: value
        for key, value in forecast.items()
        if key not in {"series", "dev_series", "train_actual"}
    }
    timestamps = pd.to_datetime(usable[TIMESTAMP], utc=True)
    return {
        "release": "v0.1",
        "dataset": {
            "name": "Open Power System Data time series",
            "version": OPSD_VERSION,
            "doi": OPSD_DOI,
            "package_url": OPSD_PACKAGE_URL,
            "primary_source": "ENTSO-E Transparency via OPSD",
            "region": "DE-LU bidding zone",
            "usable_actual_and_forecast_rows": int(len(usable)),
            "date_min": timestamps.min().isoformat(),
            "date_max": timestamps.max().isoformat(),
            "actual_column": ACTUAL,
            "forecast_column": TSO_FORECAST,
            "file_sha256": sha256_file(dataset.path),
        },
        "protocol": {
            "forecast_horizon": "published day-ahead baseline; correction features use lags >=24h",
            "development_days": 60,
            "test_days": 60,
            "seed": seed,
        },
        "forecasting": compact_forecast,
        "uncertainty_90": uncertainty,
        "reserve_risk_95": reserve,
        "ramp_events": ramps,
        "release_gate": {
            "decision": "PASS",
            "model_promotion": forecast["promotion"]["decision"],
            "rule": (
                "benchmark passes when the source is reproducible and all forecasting, "
                "uncertainty, reserve-risk, and ramp metrics are emitted; model promotion is "
                "evaluated separately"
            ),
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
    }


def write_report(
    output: str | Path,
    data_dir: str | Path,
    *,
    download: bool = False,
    seed: int = 42,
) -> dict[str, object]:
    report = evaluate(data_dir, download=download, seed=seed)
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
