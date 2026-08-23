# v0.1 methodology

The benchmark treats the published ENTSO-E day-ahead load forecast as the operational baseline. The candidate may use the published forecast plus information that is safely historical at a day-ahead horizon: actual-load lags at 24, 48, and 168 hours, rolling statistics shifted by 24 hours, prior forecast-error history shifted by 24 hours, and deterministic calendar features.

The final 60 days are untouched test data. The preceding 60 days are development data used for candidate configuration selection and uncertainty/reserve calibration. Earlier valid rows form the training period.

## Promotion

The candidate is promoted only if its held-out MAE is at least 0.5% lower than the ENTSO-E baseline and its 95th-percentile absolute error is no worse. A rejection is retained as valid benchmark evidence.

Measured on the untouched test window, `residual_hgb_small` reduces MAE from 1,127.0 MW to 1,044.4 MW and reduces 95th-percentile absolute error from 2,650.0 MW to 2,616.7 MW, so it passes the predeclared rule.

## Operational metrics

Prediction intervals and one-sided reserve buffers are calibrated only on development residuals. Ramp events use the 95th percentile of absolute hourly load changes from the training history as the event threshold. Test event precision, recall, and F1 are then measured from predicted load ramps.

The nominal 90% intervals do not retain nominal coverage under the final test-period shift: ENTSO-E coverage is 81.74% and the candidate coverage is 82.36%. The candidate interval is narrower and slightly better covered, but v0.1 explicitly records the under-coverage rather than claiming calibrated uncertainty in production.

For the 95% one-sided reserve diagnostic, the candidate's development-calibrated upward buffer is 1,650.2 MW and is exceeded in 7.64% of test hours, compared with 20.97% for the ENTSO-E baseline's 1,689.1 MW buffer. This is an offline residual-risk diagnostic, not a prescription for physical reserve procurement.

The candidate ramp detector increases precision from 76.32% to 81.82%, reduces recall from 96.67% to 90.00%, and moves F1 from 0.8529 to 0.8571 on the held-out period.

These metrics are offline analytical evidence. They do not claim live dispatch integration, guaranteed reserve sufficiency, real-time security assessment, or grid-security performance.
