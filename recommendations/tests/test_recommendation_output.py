"""
Unit and integration tests for the recommendation output module and main workflow.

Sprint: 1
Ticket: AIML-0011-W1-04
Team: AIML-04
Client: BookMyShow (Fictional)

Test Coverage:
1. Saving a valid recommendations dictionary.
2. Verifying that the generated JSON file exists.
3. Verifying that JSON content matches the original dictionary.
4. Saving to a directory that does not already exist (auto-creation).
5. Handling an empty recommendations dictionary.
6. Handling invalid output paths (None, non-str, empty string, directories).
7. Handling invalid recommendations data types.
8. Verifying UTF-8 encoding and pretty-print indentation formatting.
9. Handling file-writing errors and IOExceptions.
10. End-to-end integration: Load CSV -> Recommend -> Save JSON -> Validate.
11. Main script CLI execution and argument parsing.
12. Main script missing-file handling.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from unittest.mock import patch
import pytest

# Ensure recommendations root and src directory are on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from src.data_processing import load_data
from src.main import generate_recommendations, main
from src.recommendation_engine import recommend_events
from src.recommendation_output import save_recommendations


# ============================================================================
# 1. Unit Tests: save_recommendations() Functionality
# ============================================================================


def test_save_valid_recommendations(tmp_path: Path):
    """Verify that a valid recommendations dictionary is saved and returns resolved path."""
    recs = {
        "U001": ["E101", "E102"],
        "U002": ["E103", "E104"],
    }
    output_file = tmp_path / "recommendations.json"

    result_path = save_recommendations(recs, output_file)

    assert result_path is not None
    assert isinstance(result_path, Path)
    assert result_path.exists()
    assert result_path.is_file()
    assert result_path.stat().st_size > 0


def test_saved_json_matches_original_content(tmp_path: Path):
    """Verify that saved JSON file content matches the input recommendations dict exactly."""
    recs = {
        "U001": ["E101", "E102"],
        "U002": ["E103", "E104", "E105"],
        "U003": [],
    }
    output_file = tmp_path / "matched_recs.json"

    save_recommendations(recs, output_file)

    with open(output_file, "r", encoding="utf-8") as f:
        loaded_data = json.load(f)

    assert loaded_data == recs
    assert list(loaded_data.keys()) == ["U001", "U002", "U003"]
    assert loaded_data["U001"] == ["E101", "E102"]
    assert loaded_data["U002"] == ["E103", "E104", "E105"]
    assert loaded_data["U003"] == []


def test_saved_json_is_formatted_and_readable(tmp_path: Path):
    """Verify that saved JSON is pretty-printed with indentation and newlines."""
    recs = {"U001": ["E101", "E102"]}
    output_file = tmp_path / "pretty.json"

    save_recommendations(recs, output_file, indent=4)

    raw_text = output_file.read_text(encoding="utf-8")
    assert "\n" in raw_text
    assert "    " in raw_text  # 4-space indentation
    assert raw_text.endswith("\n")


def test_save_creates_parent_directory_automatically(tmp_path: Path):
    """Verify that non-existent parent directories are created automatically."""
    deep_dir = tmp_path / "nested" / "sub_folder" / "deep_dir"
    assert not deep_dir.exists()

    output_file = deep_dir / "recommendations.json"
    recs = {"U001": ["E101"]}

    result_path = save_recommendations(recs, output_file)

    assert deep_dir.exists()
    assert deep_dir.is_dir()
    assert result_path.exists()
    assert result_path.is_file()


def test_save_empty_recommendations_dictionary(tmp_path: Path):
    """Verify that saving an empty dictionary succeeds and produces valid JSON."""
    empty_recs = {}
    output_file = tmp_path / "empty.json"

    result_path = save_recommendations(empty_recs, output_file)

    assert result_path.exists()
    with open(result_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded == {}


def test_save_preserves_user_ids_and_event_order(tmp_path: Path):
    """Verify user IDs (including numerical or custom strings) and event sequence order are strictly preserved."""
    recs = {
        "001": ["E999", "E100", "E500"],
        "USER_ALPHA": ["EVENT_Z", "EVENT_A"],
    }
    output_file = tmp_path / "order_test.json"

    save_recommendations(recs, output_file)

    with open(output_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    assert list(loaded.keys()) == ["001", "USER_ALPHA"]
    assert loaded["001"] == ["E999", "E100", "E500"]
    assert loaded["USER_ALPHA"] == ["EVENT_Z", "EVENT_A"]


def test_save_utf8_encoding(tmp_path: Path):
    """Verify that UTF-8 multi-byte characters in IDs or metadata serialize properly."""
    recs = {
        "U_MUMBAI": ["E_संगीत_101", "E_CINÉ_102"],
    }
    output_file = tmp_path / "utf8_test.json"

    save_recommendations(recs, output_file)

    content = output_file.read_text(encoding="utf-8")
    assert "संगीत" in content
    assert "CINÉ" in content


# ============================================================================
# 2. Error Handling & Edge Cases for save_recommendations()
# ============================================================================


def test_save_raises_type_error_for_invalid_recommendations(tmp_path: Path):
    """Verify TypeError when recommendations is None or not a Mapping."""
    out_file = tmp_path / "err.json"

    with pytest.raises(TypeError, match="Expected 'recommendations' to be a dict/mapping"):
        save_recommendations(None, out_file)

    with pytest.raises(TypeError, match="Expected 'recommendations' to be a dict/mapping"):
        save_recommendations(["not", "a", "dict"], out_file)

    with pytest.raises(TypeError, match="Expected 'recommendations' to be a dict/mapping"):
        save_recommendations("string_recs", out_file)


def test_save_raises_type_error_for_invalid_event_sequence(tmp_path: Path):
    """Verify TypeError when recommendations values are not sequences."""
    out_file = tmp_path / "err.json"
    invalid_recs = {"U001": 12345}

    with pytest.raises(TypeError, match="must be a sequence/list"):
        save_recommendations(invalid_recs, out_file)


def test_save_raises_type_error_for_none_output_path():
    """Verify TypeError when output_path is None."""
    with pytest.raises(TypeError, match="output_path cannot be None"):
        save_recommendations({"U001": ["E101"]}, None)


def test_save_raises_type_error_for_non_path_output():
    """Verify TypeError when output_path is not a str or Path."""
    with pytest.raises(TypeError, match="output_path must be a string or Path-like object"):
        save_recommendations({"U001": ["E101"]}, 12345)


def test_save_raises_value_error_for_empty_output_path():
    """Verify ValueError when output_path is an empty string."""
    with pytest.raises(ValueError, match="output_path cannot be an empty string"):
        save_recommendations({"U001": ["E101"]}, "   ")


def test_save_raises_error_when_output_path_is_existing_directory(tmp_path: Path):
    """Verify IsADirectoryError when output_path points to an existing directory."""
    with pytest.raises((IsADirectoryError, ValueError), match="existing directory"):
        save_recommendations({"U001": ["E101"]}, tmp_path)


def test_save_file_writing_error_handling(tmp_path: Path):
    """Verify IOError is raised when file writing fails."""
    output_file = tmp_path / "unwritable.json"

    with patch("builtins.open", side_effect=OSError("Disk write error")):
        with pytest.raises(IOError, match="Failed to write recommendations JSON"):
            save_recommendations({"U001": ["E101"]}, output_file)


# ============================================================================
# 3. End-to-End Main Workflow & Integration Tests
# ============================================================================


def test_full_recommendation_workflow(tmp_path: Path):
    """
    Test the complete recommendation workflow:
    CSV Dataset -> load_data -> recommend_events -> save_recommendations -> JSON file.
    """
    dataset_path = BASE_DIR / "data" / "user_event_history.csv"
    assert dataset_path.exists(), f"Sample dataset missing at {dataset_path}"

    output_path = tmp_path / "output_recs.json"

    # Step 1: Ingest & clean
    df = load_data(dataset_path)
    assert not df.empty
    assert "user_id" in df.columns
    assert "event_id" in df.columns

    # Step 2: Generate recommendations
    recs = recommend_events(df, n_recommendations=3)
    assert isinstance(recs, dict)
    assert len(recs) == df["user_id"].nunique()

    # Step 3: Save to JSON
    saved_path = save_recommendations(recs, output_path)
    assert saved_path.exists()

    # Step 4: Validate JSON content
    with open(saved_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    assert json_data == recs
    for uid, event_list in json_data.items():
        assert isinstance(event_list, list)
        assert len(event_list) <= 3
        # Ensure recommended events were not previously attended by user
        attended = set(df[df["user_id"] == uid]["event_id"].unique())
        for rec_evt in event_list:
            assert rec_evt not in attended


def test_generate_recommendations_function(tmp_path: Path):
    """Verify that main.generate_recommendations orchestrates workflow and produces file."""
    dataset_path = BASE_DIR / "data" / "user_event_history.csv"
    output_path = tmp_path / "gen_recs.json"

    result = generate_recommendations(
        history_file_path=dataset_path,
        output_file_path=output_path,
        n_recommendations=3,
    )

    assert isinstance(result, dict)
    assert len(result) > 0
    assert output_path.exists()

    with open(output_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded == result


def test_main_cli_execution_with_custom_args(tmp_path: Path):
    """Verify that main() executes cleanly with CLI argument overrides."""
    dataset_path = BASE_DIR / "data" / "user_event_history.csv"
    output_path = tmp_path / "cli_recs.json"

    exit_code = main([
        "--input", str(dataset_path),
        "--output", str(output_path),
        "-n", "2",
    ])

    assert exit_code == 0
    assert output_path.exists()

    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check that each user has at most 2 recommendations
    for uid, events in data.items():
        assert len(events) <= 2


def test_main_handles_missing_dataset_gracefully(tmp_path: Path):
    """Verify that main() returns non-zero error exit code when input file does not exist."""
    fake_csv = tmp_path / "non_existent_dataset.csv"
    out_json = tmp_path / "recs.json"

    exit_code = main(["--input", str(fake_csv), "--output", str(out_json)])

    assert exit_code == 1
    assert not out_json.exists()
