"""
Data loading and preprocessing module for the BookMyShow Recommendations Service.

Sprint: 1
Ticket: AIML-0011-W1-02
Team: AIML-04

Provides data loading, schema validation, data type correction, missing-value
handling, timestamp conversion, and cleaning for user event interaction data.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Union

import pandas as pd
from pandas.errors import EmptyDataError

REQUIRED_COLUMNS: list[str] = ["user_id", "event_id", "timestamp"]


def normalize_column_names(columns: list[str]) -> list[str]:
    """
    Normalize column headers by stripping whitespace and converting to lowercase.

    If converting to lowercase would create duplicate column names (e.g. 'user_id'
    and 'User_Id' both present), the original casing is preserved for collisions
    to avoid unintended column loss or duplicate column names.

    :param columns: List of raw column headers from CSV.
    :return: List of normalized column name strings.
    """
    normalized: list[str] = []
    seen: set[str] = set()

    for col in columns:
        cleaned = str(col).strip() if isinstance(col, str) else str(col)
        candidate = cleaned.lower()
        if candidate in seen:
            normalized.append(cleaned)
            seen.add(cleaned)
        else:
            normalized.append(candidate)
            seen.add(candidate)

    return normalized


def load_data(file_path: Union[str, Path, os.PathLike]) -> pd.DataFrame:
    """
    Load and preprocess user event history data from a CSV file.

    Workflow:
    1. Validates that the input path is valid, non-null, and points to an existing file.
    2. Inspects header to map identifier columns and avoid losing leading zeros.
    3. Loads the CSV using pandas.
    4. Normalizes column names (trims whitespace and converts to lowercase).
    5. Validates that required columns ('user_id', 'event_id', 'timestamp') exist.
    6. Strips unnecessary whitespace from identifier columns.
    7. Casts 'user_id' and 'event_id' to pandas string dtype (preserving leading zeros).
    8. Converts 'timestamp' into pandas datetime format, safely coercing invalid dates.
    9. Removes rows with missing or blank required values (nulls, empty strings, NaT).
    10. Preserves any additional columns present in the dataset.
    11. Resets the DataFrame index cleanly.

    :param file_path: Path to the user event history CSV file.
    :return: Cleaned and validated pandas DataFrame.
    :raises TypeError: If file_path is None or not a string / PathLike object.
    :raises FileNotFoundError: If the CSV file does not exist.
    :raises EmptyDataError: If the CSV file is empty (0 bytes or no columns).
    :raises ValueError: If the path is a directory or required columns are missing.
    """
    if file_path is None:
        raise TypeError("file_path cannot be None; expected a valid file path string or Path.")

    if not isinstance(file_path, (str, Path, os.PathLike)):
        raise TypeError(
            f"file_path must be a string or Path-like object, got {type(file_path).__name__}"
        )

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found at: '{file_path}'")

    if path.is_dir():
        raise ValueError(f"Expected a CSV file path, but received a directory: '{file_path}'")

    if path.stat().st_size == 0:
        raise EmptyDataError(f"Dataset file at '{file_path}' is empty (0 bytes).")

    # Step 1: Read the header row to detect raw column names and preserve leading zeros
    try:
        header_df = pd.read_csv(path, nrows=0)
    except EmptyDataError as exc:
        raise EmptyDataError(
            f"Dataset at '{file_path}' contains no columns or parseable data."
        ) from exc
    except Exception as exc:
        raise ValueError(f"Failed to parse CSV header from '{file_path}': {exc}") from exc

    raw_columns = list(header_df.columns)
    if not raw_columns:
        raise EmptyDataError(f"Dataset file at '{file_path}' contains no columns.")

    # Normalize column names
    normalized_cols = normalize_column_names(raw_columns)

    # Map raw identifier columns to str to avoid losing leading zeros (e.g. '001')
    dtype_overrides: dict[str, type] = {}
    for raw_col, norm_col in zip(raw_columns, normalized_cols):
        if norm_col in ("user_id", "event_id"):
            dtype_overrides[raw_col] = str

    # Step 2: Read complete dataset with designated string dtypes for identifiers
    try:
        df = pd.read_csv(path, dtype=dtype_overrides)
    except EmptyDataError as exc:
        raise EmptyDataError(f"Dataset at '{file_path}' is empty.") from exc
    except Exception as exc:
        raise ValueError(f"Error reading dataset from '{file_path}': {exc}") from exc

    # Assign normalized column headers
    df.columns = normalized_cols

    # Step 3: Validate presence of all required columns
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(
            f"Missing required column(s): {missing_columns}. "
            f"Required columns: {REQUIRED_COLUMNS}. Available columns: {list(df.columns)}"
        )

    # Step 4: Clean and correct identifier columns
    # Strip whitespace, convert to pandas string dtype, treat empty strings as NA
    df["user_id"] = df["user_id"].astype("string").str.strip().replace("", pd.NA)
    df["event_id"] = df["event_id"].astype("string").str.strip().replace("", pd.NA)

    # Step 5: Convert timestamp to pandas datetime dtype with safe error coercion
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Step 6: Drop rows missing any required values (empty/NA user_id, event_id, or NaT timestamp)
    clean_df = df.dropna(subset=REQUIRED_COLUMNS).reset_index(drop=True)

    return clean_df


if __name__ == "__main__":
    import sys

    sample_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.path.join(os.path.dirname(__file__), "..", "data", "sample_user_event_history.csv")
    )

    try:
        result_df = load_data(sample_path)
        print("Data loaded and cleaned successfully:")
        print(result_df)
        print("\nData Types:")
        print(result_df.dtypes)
    except Exception as error:
        print(f"Error executing load_data: {error}", file=sys.stderr)
        sys.exit(1)
