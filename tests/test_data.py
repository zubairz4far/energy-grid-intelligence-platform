import pandas as pd

from grid_intelligence.data import ACTUAL, TIMESTAMP, TSO_FORECAST, usable_load_rows


def test_usable_rows_require_positive_actual_and_forecast() -> None:
    frame = pd.DataFrame(
        {
            TIMESTAMP: pd.date_range("2020-01-01", periods=4, freq="h", tz="UTC"),
            ACTUAL: [10.0, 0.0, 12.0, 13.0],
            TSO_FORECAST: [11.0, 11.0, -1.0, 14.0],
        }
    )
    result = usable_load_rows(frame)
    assert len(result) == 2
    assert result[ACTUAL].tolist() == [10.0, 13.0]
