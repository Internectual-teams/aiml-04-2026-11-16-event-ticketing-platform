"""
Unit tests for data loading and preprocessing module.

Sprint: 1
Ticket: AIML-0011-W1-02
Team: AIML-04
"""

import sys
from pathlib import Path

import pandas as pd
import pytest
from pandas.errors import EmptyDataError

# Ensure 'recommendations' root and 'src' directory are on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from src.data_processing import REQUIRED_COLUMNS, load_data, normalize_column_names


@pytest.fixture
def sample_valid_csv(tmp_path: Path) -> Path:
    """Fixture providing a valid synthetic user event history CSV."""
    file_path = tmp_path / "valid_event_history.csv"
    content = (
        "user_id,event_id,timestamp\n"
        "user_001,event_101,2026-11-15 10:30:00\n"
        "user_002,event_102,2026-11-15 11:45:00\n"
        "user_003,event_103,2026-11-15 14:20:00\n"
        "user_001,event_104,2026-11-16 09:15:00\n"
    )
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_load_valid_csv(sample_valid_csv: Path):
    """Verify that a valid CSV file is loaded successfully with expected shape."""
    df = load_data(sample_valid_csv)
    assert df is not None
    assert len(df) == 4
    assert list(df.columns) == REQUIRED_COLUMNS


def test_return_type_is_dataframe(sample_valid_csv: Path):
    """Verify that load_data returns an instance of pandas DataFrame."""
    df = load_data(sample_valid_csv)
    assert isinstance(df, pd.DataFrame)


def test_user_id_dtype_and_leading_zeros(tmp_path: Path):
    """Verify user_id has pandas string dtype and preserves leading zeros."""
    file_path = tmp_path / "leading_zeros.csv"
    content = (
        "user_id,event_id,timestamp\n"
        "001,event_101,2026-11-15 10:30:00\n"
        "002,event_102,2026-11-15 11:45:00\n"
    )
    file_path.write_text(content, encoding="utf-8")

    df = load_data(file_path)
    assert isinstance(df["user_id"].dtype, pd.StringDtype)
    assert df["user_id"].iloc[0] == "001"
    assert df["user_id"].iloc[1] == "002"


def test_event_id_dtype_and_leading_zeros(tmp_path: Path):
    """Verify event_id has pandas string dtype and preserves leading zeros."""
    file_path = tmp_path / "event_leading_zeros.csv"
    content = (
        "user_id,event_id,timestamp\n"
        "user_01,0099,2026-11-15 10:30:00\n"
        "user_02,0100,2026-11-15 11:45:00\n"
    )
    file_path.write_text(content, encoding="utf-8")

    df = load_data(file_path)
    assert isinstance(df["event_id"].dtype, pd.StringDtype)
    assert df["event_id"].iloc[0] == "0099"
    assert df["event_id"].iloc[1] == "0100"


def test_timestamp_dtype(sample_valid_csv: Path):
    """Verify timestamp is converted to pandas datetime dtype."""
    df = load_data(sample_valid_csv)
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
    assert df["timestamp"].iloc[0] == pd.Timestamp("2026-11-15 10:30:00")


def test_handling_missing_required_values(tmp_path: Path):
    """Verify that rows with missing required values (nulls) are dropped."""
    file_path = tmp_path / "missing_values.csv"
    content = (
        "user_id,event_id,timestamp\n"
        "user_001,event_101,2026-11-15 10:30:00\n"
        ",event_102,2026-11-15 11:45:00\n"  # missing user_id
        "user_003,,2026-11-15 14:20:00\n"  # missing event_id
        "user_004,event_104,\n"  # missing timestamp
        "user_005,event_105,2026-11-16 10:00:00\n"
    )
    file_path.write_text(content, encoding="utf-8")

    df = load_data(file_path)
    assert len(df) == 2
    assert list(df["user_id"]) == ["user_001", "user_005"]
    assert list(df["event_id"]) == ["event_101", "event_105"]


def test_handling_invalid_timestamps(tmp_path: Path):
    """Verify that rows containing invalid/unparseable timestamps are removed."""
    file_path = tmp_path / "invalid_timestamps.csv"
    content = (
        "user_id,event_id,timestamp\n"
        "user_001,event_101,2026-11-15 10:30:00\n"
        "user_002,event_102,invalid-datetime-string\n"
        "user_003,event_103,2026-99-99 25:99:99\n"
        "user_004,event_104,2026-11-16 12:00:00\n"
    )
    file_path.write_text(content, encoding="utf-8")

    df = load_data(file_path)
    assert len(df) == 2
    assert list(df["user_id"]) == ["user_001", "user_004"]


def test_removing_blank_identifiers(tmp_path: Path):
    """Verify that rows with empty or whitespace-only identifiers are dropped."""
    file_path = tmp_path / "blank_identifiers.csv"
    content = (
        "user_id,event_id,timestamp\n"
        "user_001,event_101,2026-11-15 10:30:00\n"
        "   ,event_102,2026-11-15 11:45:00\n"  # whitespace user_id
        "user_003,   ,2026-11-15 14:20:00\n"  # whitespace event_id
        "   ,   ,2026-11-15 15:00:00\n"  # both whitespace
        "user_004,event_104,2026-11-16 16:00:00\n"
    )
    file_path.write_text(content, encoding="utf-8")

    df = load_data(file_path)
    assert len(df) == 2
    assert list(df["user_id"]) == ["user_001", "user_004"]


def test_whitespace_stripped_from_valid_identifiers(tmp_path: Path):
    """Verify leading and trailing whitespace is stripped from identifier columns."""
    file_path = tmp_path / "whitespace_identifiers.csv"
    content = (
        "user_id,event_id,timestamp\n"
        "  user_001  ,  event_101  ,2026-11-15 10:30:00\n"
        "\tuser_002\t,\tevent_102\t,2026-11-15 11:45:00\n"
    )
    file_path.write_text(content, encoding="utf-8")

    df = load_data(file_path)
    assert df["user_id"].tolist() == ["user_001", "user_002"]
    assert df["event_id"].tolist() == ["event_101", "event_102"]


def test_missing_required_columns_raises_value_error(tmp_path: Path):
    """Verify ValueError is raised when required columns are missing."""
    file_path = tmp_path / "missing_cols.csv"
    content = "user_id,timestamp\nuser_001,2026-11-15 10:30:00\n"
    file_path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="Missing required column"):
        load_data(file_path)


def test_nonexistent_file_path_raises_file_not_found():
    """Verify FileNotFoundError is raised when file does not exist."""
    nonexistent_path = "data/non_existent_file_xyz_12345.csv"
    with pytest.raises(FileNotFoundError, match="Dataset file not found"):
        load_data(nonexistent_path)


def test_empty_csv_file_raises_empty_data_error(tmp_path: Path):
    """Verify EmptyDataError is raised when loading an empty (0-byte) CSV."""
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("", encoding="utf-8")

    with pytest.raises(EmptyDataError):
        load_data(empty_file)


def test_preserving_additional_columns(tmp_path: Path):
    """Verify that additional useful columns (e.g. rating, category) are preserved."""
    file_path = tmp_path / "extra_columns.csv"
    content = (
        "user_id,event_id,timestamp,rating,category\n"
        "user_001,event_101,2026-11-15 10:30:00,4.5,Music\n"
        "user_002,event_102,2026-11-15 11:45:00,5.0,Theatre\n"
    )
    file_path.write_text(content, encoding="utf-8")

    df = load_data(file_path)
    assert "rating" in df.columns
    assert "category" in df.columns
    assert df["rating"].tolist() == [4.5, 5.0]
    assert df["category"].tolist() == ["Music", "Theatre"]


def test_reset_index_after_cleaning(tmp_path: Path):
    """Verify that the DataFrame index is cleanly reset after rows are dropped."""
    file_path = tmp_path / "reset_index.csv"
    content = (
        "user_id,event_id,timestamp\n"
        "user_001,event_101,2026-11-15 10:30:00\n"
        ",,invalid\n"  # Dropped row
        ",,invalid\n"  # Dropped row
        "user_002,event_102,2026-11-15 11:45:00\n"
        ",,invalid\n"  # Dropped row
        "user_003,event_103,2026-11-15 12:00:00\n"
    )
    file_path.write_text(content, encoding="utf-8")

    df = load_data(file_path)
    assert len(df) == 3
    assert list(df.index) == [0, 1, 2]


def test_column_name_normalization(tmp_path: Path):
    """Verify column headers with irregular casing and whitespace are normalized."""
    file_path = tmp_path / "irregular_headers.csv"
    content = (
        " USER_ID , event_id , Timestamp \n"
        "user_001,event_101,2026-11-15 10:30:00\n"
    )
    file_path.write_text(content, encoding="utf-8")

    df = load_data(file_path)
    assert list(df.columns) == REQUIRED_COLUMNS
    assert len(df) == 1


def test_normalize_column_names_duplicate_avoidance():
    """Verify normalize_column_names avoids duplicate collision."""
    raw = ["user_id", "User_ID", "event_id", "timestamp"]
    norm = normalize_column_names(raw)
    assert len(norm) == len(set(norm))
    assert norm[0] == "user_id"
    assert norm[1] == "User_ID"


def test_invalid_input_path_types():
    """Verify TypeError is raised when invalid types are passed to load_data."""
    with pytest.raises(TypeError, match="file_path cannot be None"):
        load_data(None)

    with pytest.raises(TypeError, match="must be a string or Path-like object"):
        load_data(12345)


def test_directory_path_raises_value_error(tmp_path: Path):
    """Verify ValueError is raised if a directory path is provided instead of a file."""
    with pytest.raises(ValueError, match="Expected a CSV file path, but received a directory"):
        load_data(tmp_path)


def test_sample_user_event_history_file_if_present():
    """Verify loading the repository sample dataset if it exists."""
    sample_path = BASE_DIR / "data" / "sample_user_event_history.csv"
    if sample_path.exists():
        df = load_data(sample_path)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 4
        assert list(df.columns) == REQUIRED_COLUMNS
