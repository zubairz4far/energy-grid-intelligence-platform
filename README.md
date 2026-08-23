# Energy Grid Intelligence Platform

[![CI](https://github.com/zubairz4far/energy-grid-intelligence-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/zubairz4far/energy-grid-intelligence-platform/actions/workflows/ci.yml)

Evaluated day-ahead load forecasting and operational risk intelligence for the Germany/Luxembourg (DE-LU) bidding zone using the Open Power System Data hourly time-series package and ENTSO-E Transparency load data.

## Status

**v0.1 — evaluated OPSD/ENTSO-E day-ahead benchmark.**

The benchmark uses **16,636 hourly observations** with both DE-LU actual load and the published ENTSO-E day-ahead load forecast from **2018-10-01 through 2020-09-30**. The final 60 days are untouched test data; the preceding 60 days are development/calibration data.

## Headline result: residual correction beats the published day-ahead forecast

The candidate is deliberately tested against the operational ENTSO-E day-ahead forecast rather than a weak persistence baseline. It may use the target-hour published forecast plus only information historical by at least 24 hours and deterministic calendar features.

| Forecast | MAE MW ↓ | RMSE MW ↓ | WAPE ↓ | Bias MW | p95 abs. error MW ↓ |
|---|---:|---:|---:|---:|---:|
| ENTSO-E day-ahead | 1,127.0 | 1,386.2 | 2.159% | -680.0 | 2,650.0 |
| **Residual HistGradientBoosting** | **1,044.4** | **1,328.2** | **2.000%** | 232.8 | **2,616.7** |

**Model decision: PROMOTE.** The residual-correction model reduces held-out MAE and WAPE by **7.33%** while also improving the 95th-percentile absolute error, satisfying the predeclared promotion rule.

Held-out underforecast energy falls from **1,301,029 MWh** to **584,353 MWh** in the hourly residual accounting used by this benchmark. This is a forecast-error diagnostic, not a monetary or reserve-procurement claim.

Machine-readable evidence: [`evals/results/v0.1_opsd_de_lu.json`](evals/results/v0.1_opsd_de_lu.json).

## Uncertainty: useful improvement, but calibration drift remains

90% symmetric intervals are calibrated only from development residuals.

| Forecast | Dev-calibrated half-width MW ↓ | Test coverage |
|---|---:|---:|
| ENTSO-E day-ahead | 1,877.4 | 81.74% |
| **Residual model** | **1,791.5** | **82.36%** |

The candidate is narrower and slightly better covered, but **neither reaches the nominal 90% target on the shifted test period**. v0.1 records this under-coverage explicitly instead of claiming solved probabilistic calibration.

## Reserve-risk diagnostic

A one-sided 95% residual buffer is calibrated on development data and evaluated for exceedance on the untouched test window.

| Forecast | Upward buffer MW | Test upward exceedance ↓ | Downward buffer MW | Test downward exceedance ↓ |
|---|---:|---:|---:|---:|
| ENTSO-E day-ahead | 1,689.1 | 20.97% | 2,034.1 | **2.08%** |
| Residual model | **1,650.2** | **7.64%** | **1,990.7** | 8.40% |

These are offline residual-risk diagnostics only. They are not recommendations for physical reserve procurement or evidence of system-security sufficiency.

## Ramp-event intelligence

A high-ramp event is defined using the **95th percentile of absolute hourly load changes in training history**, measured at **4,990.95 MW/hour**. The same frozen threshold is applied to actual and predicted test ramps.

| Forecast | Precision ↑ | Recall ↑ | F1 ↑ |
|---|---:|---:|---:|
| ENTSO-E day-ahead | 76.32% | **96.67%** | 0.8529 |
| **Residual model** | **81.82%** | 90.00% | **0.8571** |

The correction model trades some recall for fewer false ramp alarms and a slightly higher held-out F1.

## Temporal evaluation contract

```text
earlier valid history                 development                 untouched test
|-----------------------------------|------ 60 days ------|--------- 60 days ---------|
       11,433 rows                       1,440 rows                 1,440 rows
       model training               selection + calibration       final evaluation
```

Day-ahead leakage controls:

- actual-load predictors use lags of **24, 48, or 168 hours**;
- rolling load statistics are shifted by 24 hours before aggregation;
- prior ENTSO-E forecast-error features are shifted by 24 hours;
- the target-hour ENTSO-E forecast is allowed because it is the published operational baseline;
- no target-period actual load or generation value is used as a predictor;
- candidate configuration selection and interval/reserve calibration use development data only.

## Promotion rule

The selected candidate is promoted only if, on the untouched final 60 days:

1. candidate MAE is at most **99.5%** of ENTSO-E day-ahead MAE; and
2. candidate 95th-percentile absolute error is no worse than ENTSO-E.

The rule is fixed before test evaluation.

## Data integrity and attribution

Open Power System Data, **Time series**, version `2020-10-06`, DOI `10.25832/time_series/2020-10-06`. OPSD documents the package as hourly load, wind, solar and price data aggregated by country/control area/bidding zone; this release uses DE-LU actual-load and day-ahead-forecast fields sourced from ENTSO-E Transparency.

Raw upstream data is not committed. The benchmark downloads the OPSD CSV and rejects any file that does not match the measured SHA256:

```text
6a7f2bc571314cbf9c321cc03437691cd4be95c3a6f075e60ff99e8035c704c8
```

Upstream attribution and source terms continue to apply.

## Reproduce

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements-ci.txt
pip install -e . --no-deps

ruff check .
pytest -q
grid-intelligence benchmark \
  --download \
  --data-dir .cache/opsd \
  --output evals/results/v0.1_opsd_de_lu.json
```

CI reruns the full public-data benchmark and requires an **exact diff** against the frozen JSON evidence before the benchmark job passes.

Full methodology and limitations: [`docs/methodology-v0.1.md`](docs/methodology-v0.1.md).

## Limitations

This is offline benchmark evidence, not live grid deployment. It does not claim production latency/SLOs, real-time dispatch integration, guaranteed reserve adequacy, causal grid-event diagnosis, or operational savings. The observed interval under-coverage is an explicit next research gap.

## License

Repository code: MIT. Raw OPSD/ENTSO-E data is not redistributed; upstream source terms and attribution apply.
