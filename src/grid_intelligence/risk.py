from __future__ import annotations

import numpy as np


def interval_metrics(
    dev_actual: np.ndarray,
    dev_predicted: np.ndarray,
    test_actual: np.ndarray,
    test_predicted: np.ndarray,
    *,
    coverage: float = 0.90,
) -> dict[str, float]:
    dev_error = np.abs(
        np.asarray(dev_actual, dtype=float) - np.asarray(dev_predicted, dtype=float)
    )
    half_width = float(np.quantile(dev_error, coverage))
    actual = np.asarray(test_actual, dtype=float)
    predicted = np.asarray(test_predicted, dtype=float)
    covered = (actual >= predicted - half_width) & (actual <= predicted + half_width)
    return {
        "target_coverage": coverage,
        "calibrated_half_width_mw": half_width,
        "test_coverage": float(np.mean(covered)),
        "mean_interval_width_mw": 2.0 * half_width,
    }


def reserve_metrics(
    dev_actual: np.ndarray,
    dev_predicted: np.ndarray,
    test_actual: np.ndarray,
    test_predicted: np.ndarray,
    *,
    quantile: float = 0.95,
) -> dict[str, float]:
    dev_residual = np.asarray(dev_actual, dtype=float) - np.asarray(dev_predicted, dtype=float)
    upward_buffer = float(np.quantile(np.clip(dev_residual, 0.0, None), quantile))
    downward_buffer = float(np.quantile(np.clip(-dev_residual, 0.0, None), quantile))
    test_residual = np.asarray(test_actual, dtype=float) - np.asarray(test_predicted, dtype=float)
    return {
        "calibration_quantile": quantile,
        "upward_buffer_mw": upward_buffer,
        "downward_buffer_mw": downward_buffer,
        "upward_exceedance_rate": float(np.mean(test_residual > upward_buffer)),
        "downward_exceedance_rate": float(np.mean(-test_residual > downward_buffer)),
    }


def _event_scores(
    actual_events: np.ndarray, predicted_events: np.ndarray
) -> dict[str, float | int]:
    actual_events = np.asarray(actual_events, dtype=bool)
    predicted_events = np.asarray(predicted_events, dtype=bool)
    tp = int(np.sum(actual_events & predicted_events))
    fp = int(np.sum(~actual_events & predicted_events))
    fn = int(np.sum(actual_events & ~predicted_events))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
    }


def ramp_metrics(
    train_actual: np.ndarray,
    test_actual: np.ndarray,
    test_predicted: np.ndarray,
    *,
    quantile: float = 0.95,
) -> dict[str, float | int]:
    train_actual = np.asarray(train_actual, dtype=float)
    actual = np.asarray(test_actual, dtype=float)
    predicted = np.asarray(test_predicted, dtype=float)
    threshold = float(np.quantile(np.abs(np.diff(train_actual)), quantile))
    actual_ramp = np.abs(np.diff(actual)) >= threshold
    predicted_ramp = np.abs(np.diff(predicted)) >= threshold
    return {"ramp_threshold_mw_per_hour": threshold, **_event_scores(actual_ramp, predicted_ramp)}
