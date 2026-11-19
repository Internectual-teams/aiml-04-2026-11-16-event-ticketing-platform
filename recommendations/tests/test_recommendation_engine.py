"""
Unit tests for the BookMyShow Recommendation Engine.

Sprint: 1
Ticket: AIML-0011-W1-03
Team: AIML-04

Test Coverage:
1. Normal recommendation generation.
2. Personalized recommendations for different users.
3. Popularity-based fallback.
4. Exclusion of previously attended events.
5. Duplicate recommendation prevention.
6. Empty DataFrame handling.
7. Missing-value handling.
8. Users with insufficient / no interaction history.
9. Configurable recommendation counts (top_n, n_recommendations).
10. Integration test with sample datasets.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Ensure recommendations root and src directory are on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from src.data_processing import load_data
from src.recommendation_engine import (
    calculate_event_popularity,
    get_category_events_map,
    get_user_category_affinities,
    get_user_event_history,
    recommend_events,
)


@pytest.fixture
def sample_history_df() -> pd.DataFrame:
    """Fixture providing a standard synthetic interaction DataFrame."""
    return pd.DataFrame(
        {
            "user_id": [
                "U1", "U1", "U1", "U1",
                "U2", "U2", "U2",
                "U3", "U3", "U3",
                "U4",
            ],
            "event_id": [
                "E101", "E102", "E101", "E103",
                "E201", "E202", "E201",
                "E301", "E101", "E201",
                "E101",
            ],
            "event_category": [
                "Music", "Music", "Music", "Music",
                "Comedy", "Comedy", "Comedy",
                "Theatre", "Music", "Comedy",
                "Music",
            ],
            "timestamp": pd.date_range("2026-11-10", periods=11, freq="h"),
        }
    )


@pytest.fixture
def real_dataset_df() -> pd.DataFrame:
    """Fixture providing the real preprocessed user_event_history.csv dataset."""
    csv_path = BASE_DIR / "data" / "user_event_history.csv"
    assert csv_path.exists(), f"Expected dataset at {csv_path}"
    return load_data(csv_path)


# ---------------------------------------------------------------------------
# Scenario 1: Normal Recommendation Generation
# ---------------------------------------------------------------------------


def test_normal_recommendation_generation(real_dataset_df: pd.DataFrame):
    """Verify normal recommendation generation returns the expected dictionary structure."""
    recommendations = recommend_events(real_dataset_df, n_recommendations=3)

    assert isinstance(recommendations, dict)
    assert len(recommendations) == real_dataset_df["user_id"].nunique()

    for user_id, events in recommendations.items():
        assert isinstance(user_id, str)
        assert isinstance(events, list)
        assert len(events) <= 3
        for event_id in events:
            assert isinstance(event_id, str)
            assert event_id.strip() != ""


# ---------------------------------------------------------------------------
# Scenario 2: Personalized Recommendations for Different Users
# ---------------------------------------------------------------------------


def test_personalized_recommendations_for_different_users(real_dataset_df: pd.DataFrame):
    """
    Verify that users with distinct category affinities receive distinct,
    personalized recommendations tailored to their historical preferences.
    """
    recommendations = recommend_events(real_dataset_df, n_recommendations=3)

    # U001 has strong Music preference
    # U002 has strong Theatre/Dance preference
    # U004 has strong Sports preference
    recs_u001 = recommendations["U001"]
    recs_u002 = recommendations["U002"]
    recs_u004 = recommendations["U004"]

    # Verify recommendations are personalized and differ between users
    assert recs_u001 != recs_u002
    assert recs_u001 != recs_u004

    # Verify U001 gets other Music events (e.g. E103, E115, E116)
    event_cats = real_dataset_df.groupby("event_id")["event_category"].first().to_dict()
    music_count_u001 = sum(1 for e in recs_u001 if event_cats.get(e) == "Music")
    assert music_count_u001 >= 2, "Music fan U001 should receive primarily Music recommendations"


# ---------------------------------------------------------------------------
# Scenario 3: Popularity-Based Fallback
# ---------------------------------------------------------------------------


def test_popularity_based_fallback_when_category_exhausted():
    """
    Verify that when all events in a user's preferred category are already attended,
    the engine gracefully falls back to globally popular events from other categories.
    """
    # Create dataset where User A attended all Music events
    df = pd.DataFrame(
        {
            "user_id": ["UA", "UA", "UB", "UB", "UC", "UC"],
            "event_id": ["E_M1", "E_M2", "E_M1", "E_C1", "E_C1", "E_T1"],
            "event_category": ["Music", "Music", "Music", "Comedy", "Comedy", "Theatre"],
            "timestamp": pd.date_range("2026-11-15", periods=6, freq="D"),
        }
    )
    # UA has attended both E_M1 and E_M2 (all Music events)
    recs = recommend_events(df, n_recommendations=2, user_id="UA")

    assert "UA" in recs
    assert len(recs["UA"]) == 2
    # Since Music is exhausted, it must fall back to popular Comedy (E_C1) and Theatre (E_T1)
    assert recs["UA"] == ["E_C1", "E_T1"]
    assert "E_M1" not in recs["UA"]
    assert "E_M2" not in recs["UA"]


def test_fallback_when_category_column_missing():
    """Verify that if 'event_category' is omitted, pure popularity ranking is used."""
    df = pd.DataFrame(
        {
            "user_id": ["U1", "U2", "U2", "U3", "U3", "U3"],
            "event_id": ["E1", "E1", "E2", "E1", "E2", "E3"],
        }
    )
    # Popularity: E1 (3), E2 (2), E3 (1)
    recs = recommend_events(df, n_recommendations=2)

    # U1 attended E1 -> should get E2, E3
    assert recs["U1"] == ["E2", "E3"]
    # U2 attended E1, E2 -> should get E3
    assert recs["U2"] == ["E3"]


# ---------------------------------------------------------------------------
# Scenario 4: Exclusion of Previously Attended Events
# ---------------------------------------------------------------------------


def test_exclusion_of_previously_attended_events(real_dataset_df: pd.DataFrame):
    """Verify that no recommended event is one the user has previously interacted with."""
    user_history = get_user_event_history(real_dataset_df)
    recommendations = recommend_events(real_dataset_df, n_recommendations=5)

    for user_id, rec_events in recommendations.items():
        attended = user_history.get(user_id, set())
        for event in rec_events:
            assert event not in attended, (
                f"User {user_id} was recommended previously attended event {event}!"
            )


# ---------------------------------------------------------------------------
# Scenario 5: Duplicate Recommendation Prevention
# ---------------------------------------------------------------------------


def test_duplicate_recommendation_prevention():
    """Verify recommendations contain no duplicate event IDs even with repeated interactions."""
    # Dataset with many repeated interactions for the same events
    df = pd.DataFrame(
        {
            "user_id": ["U1"] * 10 + ["U2"] * 5,
            "event_id": [
                "E1", "E1", "E1", "E2", "E2", "E3", "E3", "E4", "E4", "E5",
                "E1", "E2", "E2", "E3", "E4",
            ],
            "event_category": ["CatA"] * 15,
            "timestamp": pd.date_range("2026-11-01", periods=15, freq="h"),
        }
    )
    recommendations = recommend_events(df, n_recommendations=5)

    for user_id, events in recommendations.items():
        # Check no duplicates
        assert len(events) == len(set(events)), (
            f"Duplicate event IDs found in recommendations for {user_id}: {events}"
        )


# ---------------------------------------------------------------------------
# Scenario 6: Empty DataFrame Handling
# ---------------------------------------------------------------------------


def test_empty_dataframe_handling():
    """Verify that empty DataFrames are handled safely without raising exceptions."""
    # Completely empty DataFrame
    empty_df = pd.DataFrame()
    assert recommend_events(empty_df) == {}

    # Empty DataFrame with expected schema
    schema_empty_df = pd.DataFrame(columns=["user_id", "event_id", "event_category"])
    assert recommend_events(schema_empty_df) == {}

    # Empty DataFrame with specific user_id requested
    assert recommend_events(empty_df, user_id="U999") == {"U999": []}


# ---------------------------------------------------------------------------
# Scenario 7: Missing-Value Handling
# ---------------------------------------------------------------------------


def test_missing_value_handling():
    """Verify that nulls, empty strings, and whitespace values are handled safely."""
    df_with_nans = pd.DataFrame(
        {
            "user_id": ["U1", None, "U1", "  ", "U2", "U2", np.nan],
            "event_id": ["E1", "E2", None, "E3", "E1", "E2", "E4"],
            "event_category": ["Music", "Music", "Comedy", "Tech", None, "Comedy", "Sports"],
            "timestamp": pd.date_range("2026-11-01", periods=7, freq="D"),
        }
    )

    # Valid rows are:
    # row 0: U1, E1, Music
    # row 4: U2, E1, None
    # row 5: U2, E2, Comedy
    recommendations = recommend_events(df_with_nans, n_recommendations=2)

    assert "U1" in recommendations
    assert "U2" in recommendations
    assert "" not in recommendations
    assert "None" not in recommendations

    # U1 attended E1; U2 attended E1, E2
    # Popularity: E1 (2), E2 (1)
    # U1 can be recommended E2
    assert recommendations["U1"] == ["E2"]
    # U2 attended all valid events (E1, E2), so recs should be empty
    assert recommendations["U2"] == []


# ---------------------------------------------------------------------------
# Scenario 8: Users with Insufficient or No Interaction History (Cold Start)
# ---------------------------------------------------------------------------


def test_users_with_insufficient_interaction_history(real_dataset_df: pd.DataFrame):
    """Verify users with minimal history receive personalized + popularity backfill."""
    # U007 has only 1 interaction: E101 (Music)
    recommendations = recommend_events(real_dataset_df, n_recommendations=3, user_id="U007")

    assert "U007" in recommendations
    assert len(recommendations["U007"]) == 3
    assert "E101" not in recommendations["U007"]


def test_cold_start_user_with_zero_history(real_dataset_df: pd.DataFrame):
    """Verify that a new user with zero prior interactions receives top popular events."""
    recs = recommend_events(real_dataset_df, n_recommendations=3, user_id="BRAND_NEW_USER")

    assert "BRAND_NEW_USER" in recs
    assert len(recs["BRAND_NEW_USER"]) == 3

    # Check that recommendations match top globally popular events
    pop = calculate_event_popularity(real_dataset_df)
    top_3_popular = list(pop.index[:3])
    assert recs["BRAND_NEW_USER"] == top_3_popular


# ---------------------------------------------------------------------------
# Scenario 9: Configurable Parameters & Validation
# ---------------------------------------------------------------------------


def test_configurable_n_recommendations(real_dataset_df: pd.DataFrame):
    """Verify that n_recommendations (and kwargs aliases) accurately limits recommendations."""
    # Test n=1
    recs_1 = recommend_events(real_dataset_df, n_recommendations=1)
    for user, events in recs_1.items():
        assert len(events) <= 1

    # Test n=5
    recs_5 = recommend_events(real_dataset_df, n_recommendations=5)
    for user, events in recs_5.items():
        assert len(events) <= 5

    # Test n=0
    recs_0 = recommend_events(real_dataset_df, n_recommendations=0)
    for user, events in recs_0.items():
        assert len(events) == 0

    # Test kwarg alias top_n
    recs_top = recommend_events(real_dataset_df, top_n=2)
    for user, events in recs_top.items():
        assert len(events) <= 2


def test_invalid_input_type():
    """Verify TypeError is raised when input is not a pandas DataFrame."""
    with pytest.raises(TypeError, match="must be a pandas DataFrame"):
        recommend_events("not a dataframe")  # type: ignore

    with pytest.raises(TypeError, match="must be a pandas DataFrame"):
        recommend_events(None)  # type: ignore


def test_missing_required_columns():
    """Verify ValueError is raised when DataFrame lacks user_id or event_id."""
    invalid_df = pd.DataFrame({"wrong_col": [1, 2, 3]})
    with pytest.raises(ValueError, match="Missing required columns"):
        recommend_events(invalid_df)


# ---------------------------------------------------------------------------
# Scenario 10: Helper Function Unit Tests
# ---------------------------------------------------------------------------


def test_calculate_event_popularity(sample_history_df: pd.DataFrame):
    """Verify popularity calculation accurately sums interaction frequencies."""
    popularity = calculate_event_popularity(sample_history_df)

    # In sample_history_df:
    # E101 appears 4 times (U1 x 2, U3 x 1, U4 x 1)
    # E201 appears 3 times (U2 x 2, U3 x 1)
    # E102, E103, E202, E301 each appear 1 time
    assert popularity["E101"] == 4
    assert popularity["E201"] == 3
    assert popularity["E102"] == 1
    assert list(popularity.index[:2]) == ["E101", "E201"]


def test_get_user_category_affinities(sample_history_df: pd.DataFrame):
    """Verify category affinity ordering by interaction frequency."""
    # U1 interacted 4 times with Music
    affinities_u1 = get_user_category_affinities(sample_history_df, "U1")
    assert affinities_u1 == [("Music", 4)]

    # U3 interacted with Music (1), Comedy (1), Theatre (1)
    affinities_u3 = get_user_category_affinities(sample_history_df, "U3")
    assert len(affinities_u3) == 3
    cats = [c for c, _ in affinities_u3]
    assert set(cats) == {"Music", "Comedy", "Theatre"}


def test_sample_csv_without_category():
    """Verify that the original sample_user_event_history.csv from W1-02 works seamlessly."""
    sample_csv = BASE_DIR / "data" / "sample_user_event_history.csv"
    if sample_csv.exists():
        df = load_data(sample_csv)
        recs = recommend_events(df, n_recommendations=2)
        assert isinstance(recs, dict)
        for uid in df["user_id"].unique():
            assert uid in recs
