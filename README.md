# Energy Grid Intelligence Platform

[![CI](https://github.com/zubairz4far/energy-grid-intelligence-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/zubairz4far/energy-grid-intelligence-platform/actions/workflows/ci.yml)

Evaluated power-system load forecasting and operational risk intelligence using the Open Power System Data hourly time-series package and the Germany/Luxembourg (DE-LU) bidding-zone load published through ENTSO-E Transparency.

## v0.1 scope

- compare a residual-correction HistGradientBoosting model against the **published ENTSO-E day-ahead load forecast**, not a weak toy baseline;
- use only calendar values, the published day-ahead forecast, and load/error lags of at least 24 hours;
- freeze model selection on a development window and keep the final 60 days untouched for test;
- calibrate 90% forecast intervals on development residuals;
- estimate one-sided 95% upward/downward reserve buffers from development errors and evaluate exceedance on test;
- detect high-ramp hours using a threshold learned from historical actual load changes;
- preserve an explicit model promotion decision separately from the repository benchmark status.

## Data

Open Power System Data, **Time series**, version `2020-10-06`, DOI `10.25832/time_series/2020-10-06`. The package aggregates hourly load, generation, and price series from official sources; this benchmark uses the DE-LU actual-load and day-ahead-forecast fields whose primary source is ENTSO-E Transparency.

Raw upstream data is downloaded during the benchmark and is not committed to this repository. Upstream attribution and source terms continue to apply.

## Evaluation contract

```text
earlier valid history                 development                 untouched test
|-----------------------------------|------ 60 days ------|--------- 60 days ---------|
       model training               model selection +      forecast/risk evaluation
                                    interval calibration
```

Day-ahead leakage controls:

- actual-load features use lags of **24 hours or more**;
- rolling load features are shifted by 24 hours before aggregation;
- prior ENTSO-E forecast-error features are also shifted by 24 hours;
- the published target-hour ENTSO-E forecast is allowed because it is the operational day-ahead baseline;
- no target-period actual generation/load value is used as a predictor.

## Promotion rule

The selected residual-correction candidate is promoted only if, on the untouched final 60 days:

1. MAE is at least **0.5% lower** than the ENTSO-E day-ahead forecast; and
2. 95th-percentile absolute error is no worse than ENTSO-E.

A candidate rejection remains a valid result and is not retuned after test observation.

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

Full methodology: [`docs/methodology-v0.1.md`](docs/methodology-v0.1.md).

## Status

**v0.1 implementation complete; measured OPSD evidence pending on this pull request.** No forecasting-improvement, reserve-buffer, interval-coverage, or ramp-detection number is claimed until the real-data CI benchmark succeeds and its output is frozen.

## License

Repository code: MIT. Raw OPSD/ENTSO-E data is not redistributed; upstream source terms and attribution apply.
