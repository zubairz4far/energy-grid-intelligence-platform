# v0.1 methodology

The benchmark treats the published ENTSO-E day-ahead load forecast as the operational baseline. The candidate may use the published forecast plus information that is safely historical at a day-ahead horizon: actual-load lags at 24, 48, and 168 hours, rolling statistics shifted by 24 hours, prior forecast-error history shifted by 24 hours, and deterministic calendar features.

The final 60 days are untouched test data. The preceding 60 days are development data used for candidate configuration selection and uncertainty/reserve calibration. Earlier valid rows form the training period.

## Promotion

The candidate is promoted only if its held-out MAE is at least 0.5% lower than the ENTSO-E baseline and its 95th-percentile absolute error is no worse. A rejection is retained as valid benchmark evidence.

## Operational metrics

Prediction intervals and one-sided reserve buffers are calibrated only on development residuals. Ramp events use the 95th percentile of absolute hourly load changes from the training history as the event threshold. Test event precision, recall, and F1 are then measured from predicted load ramps.

These metrics are offline analytical evidence. They do not claim live dispatch integration, guaranteed reserve sufficiency, or grid-security performance.
