import numpy as np
import pandas as pd

from grid_intelligence.data import ACTUAL, TIMESTAMP, TSO_FORECAST
from grid_intelligence.forecasting import build_features


def _frame(hours: int = 500) -> pd.DataFrame:
    timestamp = pd.date_range("2020-01-01", periods=hours, freq="h", tz="UTC")
    values = np.arange(hours, dtype=float) + 10_000.0
    return pd.DataFrame({TIMESTAMP: timestamp, ACTUAL: values, TSO_FORECAST: values + 50.0})


def test_day_ahead_features_use_only_known_lags() -> None:
    frame = _frame()
    panel = build_features(frame)
    row = panel.iloc[-1]
    source = frame.set_index(TIMESTAMP)
    timestamp = row[TIMESTAMP]
    assert row["load_lag_24"] == source.loc[timestamp - pd.Timedelta(hours=24), ACTUAL]
    assert row["load_lag_168"] == source.loc[timestamp - pd.Timedelta(hours=168), ACTUAL]


def test_future_actual_mutation_does_not_change_earlier_feature_row() -> None:
    frame = _frame()
    original = build_features(frame)
    target_time = original.iloc[-50][TIMESTAMP]
    before = original.loc[original[TIMESTAMP] == target_time].iloc[0].copy()
    frame.loc[frame[TIMESTAMP] > target_time, ACTUAL] = 999_999.0
    after = build_features(frame)
    after_row = after.loc[after[TIMESTAMP] == target_time].iloc[0]
    for column in ["load_lag_24", "load_lag_48", "load_lag_168", "tso_error_lag_24"]:
        assert before[column] == after_row[column]
