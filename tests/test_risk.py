import numpy as np

from grid_intelligence.risk import interval_metrics, ramp_metrics, reserve_metrics


def test_interval_is_calibrated_only_from_development_errors() -> None:
    dev_actual = np.array([10.0, 20.0, 30.0, 40.0])
    dev_pred = np.array([9.0, 18.0, 27.0, 36.0])
    result = interval_metrics(
        dev_actual, dev_pred, np.array([50.0]), np.array([50.0]), coverage=0.5
    )
    assert result["calibrated_half_width_mw"] == 2.5
    assert result["test_coverage"] == 1.0


def test_reserve_buffer_reports_test_exceedance() -> None:
    dev_actual = np.array([10.0, 12.0, 14.0, 16.0])
    dev_pred = np.array([9.0, 10.0, 11.0, 12.0])
    test_actual = np.array([20.0, 20.0])
    test_pred = np.array([10.0, 30.0])
    result = reserve_metrics(dev_actual, dev_pred, test_actual, test_pred, quantile=0.75)
    assert result["upward_buffer_mw"] > 0
    assert result["upward_exceedance_rate"] == 0.5


def test_ramp_metrics_are_bounded() -> None:
    train = np.array([0.0, 1.0, 2.0, 10.0, 11.0, 12.0])
    actual = np.array([0.0, 8.0, 9.0, 17.0])
    predicted = np.array([0.0, 7.0, 8.0, 15.0])
    result = ramp_metrics(train, actual, predicted, quantile=0.8)
    assert 0.0 <= result["precision"] <= 1.0
    assert 0.0 <= result["recall"] <= 1.0
    assert result["ramp_threshold_mw_per_hour"] > 0
