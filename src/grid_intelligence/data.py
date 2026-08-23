from __future__ import annotations

import hashlib
import shutil
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

OPSD_VERSION = "2020-10-06"
OPSD_DOI = "10.25832/time_series/2020-10-06"
OPSD_PACKAGE_URL = "https://data.open-power-system-data.org/time_series/2020-10-06"
DATA_URL = (
    "https://data.open-power-system-data.org/time_series/2020-10-06/"
    "time_series_60min_singleindex.csv"
)
DATA_FILENAME = "time_series_60min_singleindex.csv"
TIMESTAMP = "utc_timestamp"
ACTUAL = "DE_LU_load_actual_entsoe_transparency"
TSO_FORECAST = "DE_LU_load_forecast_entsoe_transparency"
OPTIONAL_COLUMNS = ["DE_LU_wind_generation_actual", "DE_LU_solar_generation_actual"]
EXPECTED_SHA256: str | None = None


@dataclass(frozen=True)
class GridDataset:
    frame: pd.DataFrame
    path: Path


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "grid-intelligence-v0.1"})
    with urllib.request.urlopen(request, timeout=240) as response, temporary.open("wb") as handle:
        shutil.copyfileobj(response, handle, length=1024 * 1024)
    temporary.replace(destination)


def ensure_data_file(data_dir: str | Path, *, download: bool = False) -> Path:
    root = Path(data_dir)
    path = root / DATA_FILENAME
    if not path.exists():
        if not download:
            raise FileNotFoundError(
                f"Missing {DATA_FILENAME}. Re-run with --download or place the OPSD file in {root}."
            )
        _download(DATA_URL, path)
    if EXPECTED_SHA256 is not None:
        digest = sha256_file(path)
        if digest != EXPECTED_SHA256:
            raise ValueError(f"Unexpected OPSD SHA256: {digest}")
    return path


def load_grid_data(data_dir: str | Path, *, download: bool = False) -> GridDataset:
    path = ensure_data_file(data_dir, download=download)
    header = pd.read_csv(path, nrows=0).columns.tolist()
    required = [TIMESTAMP, ACTUAL, TSO_FORECAST]
    missing = [column for column in required if column not in header]
    if missing:
        raise ValueError(f"Missing expected OPSD columns: {missing}")
    columns = required + [column for column in OPTIONAL_COLUMNS if column in header]
    frame = pd.read_csv(path, usecols=columns, low_memory=False)
    frame[TIMESTAMP] = pd.to_datetime(frame[TIMESTAMP], utc=True, errors="coerce")
    for column in columns[1:]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=[TIMESTAMP]).sort_values(TIMESTAMP)
    frame = frame.drop_duplicates(TIMESTAMP, keep="last").set_index(TIMESTAMP)
    if frame.empty:
        raise ValueError("No timestamped rows found in OPSD file")
    full_index = pd.date_range(frame.index.min(), frame.index.max(), freq="h", tz="UTC")
    frame = frame.reindex(full_index).rename_axis(TIMESTAMP).reset_index()
    return GridDataset(frame=frame, path=path)


def usable_load_rows(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame[ACTUAL].gt(0) & frame[TSO_FORECAST].gt(0)
    return frame.loc[valid].copy().reset_index(drop=True)
