"""
Personalized Event Recommendation Engine for BookMyShow.

Sprint: 1
Ticket: AIML-0011-W1-03
Team: AIML-04
Client: BookMyShow (Fictional)

This module provides a hybrid recommendation engine combining:
1. Popularity-based candidate retrieval (interaction frequency ranking).
2. Category-based personalization (user interaction history and category affinity).
3. Personalized ranking with exclusion of previously attended events and deduplication.
4. Robust fallback mechanisms for cold-start and low-history users.
"""

from __future__ import annotations

import logging
from typing import Any, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)


def calculate_event_popularity(data: pd.DataFrame) -> pd.Series:
    """
    Calculate the total interaction frequency for each unique event.

    Popularity is defined as the total number of interactions recorded for each
    event across the dataset. Ties are broken deterministically by event ID.

    :param data: Cleaned pandas DataFrame containing at least an 'event_id' column.
    :return: A pandas Series with event_id as index and interaction count as values,
             sorted in descending order of popularity.
    """
    if data.empty or "event_id" not in data.columns:
        return pd.Series(dtype="int64")

    # Filter out missing/blank event identifiers
    valid_events = data["event_id"].dropna().astype(str).str.strip()
    valid_events = valid_events[valid_events != ""]

    if valid_events.empty:
        return pd.Series(dtype="int64")

    # Calculate interaction count per event
    counts = valid_events.value_counts()

    # Deterministic sort: descending by frequency, then ascending by event_id for ties
    sorted_df = (
        pd.DataFrame({"event_id": counts.index, "frequency": counts.values})
        .sort_values(by=["frequency", "event_id"], ascending=[False, True])
        .reset_index(drop=True)
    )

    return pd.Series(
        data=sorted_df["frequency"].values,
        index=sorted_df["event_id"].values,
        name="interaction_count",
    )


def get_user_event_history(data: pd.DataFrame) -> dict[str, set[str]]:
    """
    Identify events that each user has already attended or interacted with.

    :param data: Cleaned pandas DataFrame with 'user_id' and 'event_id' columns.
    :return: Dictionary mapping user_id to a set of unique event_id strings.
    """
    if data.empty or "user_id" not in data.columns or "event_id" not in data.columns:
        return {}

    # Extract non-null, trimmed string identifiers
    cleaned = (
        data[["user_id", "event_id"]]
        .dropna()
        .astype(str)
        .map(str.strip)
    )
    cleaned = cleaned[(cleaned["user_id"] != "") & (cleaned["event_id"] != "")]

    if cleaned.empty:
        return {}

    history: dict[str, set[str]] = {}
    grouped = cleaned.groupby("user_id")["event_id"]
    for user_id, events in grouped:
        history[user_id] = set(events)

    return history


def get_user_category_affinities(
    data: pd.DataFrame, user_id: str
) -> list[tuple[str, int]]:
    """
    Analyze user interaction history to identify category preferences.

    Counts how many times the specified user interacted with each event category,
    giving preference to categories with stronger interaction counts.

    :param data: pandas DataFrame with 'user_id' and 'event_category' columns.
    :param user_id: Identifier of the target user.
    :return: List of tuples (category_name, interaction_count) sorted by descending
             interaction frequency, then alphabetically by category name.
    """
    if "event_category" not in data.columns or data.empty:
        return []

    # Filter interactions for target user
    user_mask = data["user_id"].astype(str).str.strip() == str(user_id).strip()
    user_df = data.loc[user_mask]

    if user_df.empty:
        return []

    valid_cats = user_df["event_category"].dropna().astype(str).str.strip()
    valid_cats = valid_cats[valid_cats != ""]

    if valid_cats.empty:
        return []

    counts = valid_cats.value_counts()
    sorted_df = (
        pd.DataFrame({"category": counts.index, "count": counts.values})
        .sort_values(by=["count", "category"], ascending=[False, True])
        .reset_index(drop=True)
    )

    return list(zip(sorted_df["category"], sorted_df["count"]))


def get_category_events_map(
    data: pd.DataFrame, ranked_popular_events: list[str]
) -> dict[str, list[str]]:
    """
    Map each event category to its constituent event IDs, ordered by popularity.

    If an event is tagged with multiple categories across records, the most frequent
    category tag is used as its primary category.

    :param data: pandas DataFrame with 'event_id' and 'event_category' columns.
    :param ranked_popular_events: Globally ranked event IDs ordered from most to least popular.
    :return: Dictionary mapping category name to list of event IDs ordered by popularity.
    """
    if "event_category" not in data.columns or data.empty:
        return {}

    cleaned = (
        data[["event_id", "event_category"]]
        .dropna()
        .astype(str)
        .map(str.strip)
    )
    cleaned = cleaned[(cleaned["event_id"] != "") & (cleaned["event_category"] != "")]

    if cleaned.empty:
        return {}

    # Determine primary category for each event (mode category)
    event_primary_cat: dict[str, str] = (
        cleaned.groupby(["event_id", "event_category"])
        .size()
        .reset_index(name="cnt")
        .sort_values(by=["event_id", "cnt"], ascending=[True, False])
        .drop_duplicates(subset=["event_id"])
        .set_index("event_id")["event_category"]
        .to_dict()
    )

    # Invert mapping: category -> list of events, preserving popularity order
    category_map: dict[str, list[str]] = {}
    for event_id in ranked_popular_events:
        cat = event_primary_cat.get(event_id)
        if cat:
            category_map.setdefault(cat, []).append(event_id)

    return category_map


def recommend_events(
    data: pd.DataFrame,
    n_recommendations: int = 3,
    user_id: Optional[str] = None,
    **kwargs: Any,
) -> dict[str, list[str]]:
    """
    Recommend relevant events for users using a hybrid recommendation algorithm.

    Algorithm Workflow:
    1. Input Validation & Cleaning:
       - Ensures data is a valid pandas DataFrame.
       - Safely handles empty DataFrames, missing values, and whitespace.
       - Validates presence of required identifier columns ('user_id', 'event_id').
    2. Popularity Calculation:
       - Computes global event popularity based on interaction frequency across all users.
       - Establishes a ranked candidate pool for cold-start and fallback recommendations.
    3. User History Identification:
       - Maps each user to the set of events they have already attended or interacted with.
       - Ensures previously attended events are strictly excluded from recommendations.
    4. Category-Based Personalization:
       - Identifies category affinity for each user, prioritizing categories with the
         highest user interaction history.
       - Gathers unvisited popular events within the user's preferred categories.
    5. Hybrid Ranking & Fallback:
       - Fills remaining slots with globally popular unvisited events if category events
         are exhausted or if user has limited/no history.
       - Ensures recommendations contain no duplicate event IDs and match n_recommendations.

    :param data: Preprocessed pandas DataFrame containing user event interactions.
                 Expected columns: 'user_id', 'event_id', and optionally 'event_category'.
    :param n_recommendations: Maximum number of events to recommend per user (default: 3).
    :param user_id: Optional specific user ID to generate recommendations for.
                    If None, recommendations are generated for all users in the dataset.
    :param kwargs: Additional optional arguments (e.g., 'top_n', 'limit').
    :return: Dictionary mapping user_id string to a list of recommended event_id strings.
             Example: {"U001": ["E105", "E108", "E112"]}
    :raises TypeError: If data is not a pandas DataFrame.
    :raises ValueError: If required columns 'user_id' or 'event_id' are missing.
    """
    # Step 1: Input Validation
    if data is None or not isinstance(data, pd.DataFrame):
        raise TypeError(
            f"Input 'data' must be a pandas DataFrame, got {type(data).__name__}"
        )

    # Support alternative parameter aliases like 'top_n' or 'limit' passed in kwargs
    if "top_n" in kwargs:
        n_recommendations = kwargs["top_n"]
    elif "limit" in kwargs:
        n_recommendations = kwargs["limit"]
    elif "n" in kwargs:
        n_recommendations = kwargs["n"]

    n_recommendations = max(0, int(n_recommendations))

    # Handle empty DataFrame gracefully
    if data.empty:
        if user_id is not None:
            return {str(user_id): []}
        return {}

    # Validate required columns
    required_cols = {"user_id", "event_id"}
    missing_cols = required_cols - set(data.columns)
    if missing_cols:
        raise ValueError(
            f"Missing required columns in DataFrame: {sorted(list(missing_cols))}. "
            f"Expected at least 'user_id' and 'event_id'."
        )

    # Clean missing / empty values in identifiers
    cleaned_df = data.dropna(subset=["user_id", "event_id"]).copy()
    cleaned_df["user_id"] = cleaned_df["user_id"].astype(str).str.strip()
    cleaned_df["event_id"] = cleaned_df["event_id"].astype(str).str.strip()
    cleaned_df = cleaned_df[
        (cleaned_df["user_id"] != "") & (cleaned_df["event_id"] != "")
    ]

    if cleaned_df.empty:
        if user_id is not None:
            return {str(user_id): []}
        return {}

    # If n_recommendations is 0, return empty recommendation lists
    if n_recommendations == 0:
        if user_id is not None:
            return {str(user_id): []}
        all_uids = sorted(cleaned_df["user_id"].unique().tolist())
        return {uid: [] for uid in all_uids}

    # Step 2: Global Popularity Ranking
    popularity_series = calculate_event_popularity(cleaned_df)
    ranked_popular_events: list[str] = list(popularity_series.index)

    # Step 3: Event-to-Category Mapping (if category column is available)
    has_category = "event_category" in cleaned_df.columns
    category_events_map = (
        get_category_events_map(cleaned_df, ranked_popular_events)
        if has_category
        else {}
    )

    # Step 4: Identify Attended Events per User
    user_history = get_user_event_history(cleaned_df)

    # Step 5: Determine Target Users
    if user_id is not None:
        target_users = [str(user_id).strip()]
    else:
        target_users = sorted(cleaned_df["user_id"].unique().tolist())

    recommendations: dict[str, list[str]] = {}

    # Step 6: Generate Personalized Recommendations for Each Target User
    for uid in target_users:
        attended = user_history.get(uid, set())
        recs: list[str] = []
        seen: set[str] = set(attended)  # Exclude attended events and prevent duplicates

        # Component A: Category-Based Recommendations
        if has_category and uid in user_history:
            category_affinities = get_user_category_affinities(cleaned_df, uid)
            for category, _ in category_affinities:
                candidate_events = category_events_map.get(category, [])
                for event in candidate_events:
                    if event not in seen:
                        recs.append(event)
                        seen.add(event)
                        if len(recs) >= n_recommendations:
                            break
                if len(recs) >= n_recommendations:
                    break

        # Component B: Popularity-Based Fallback
        # If user has no previous history, exhausted category candidates,
        # or dataset has no categories, backfill with globally popular events.
        if len(recs) < n_recommendations:
            for event in ranked_popular_events:
                if event not in seen:
                    recs.append(event)
                    seen.add(event)
                    if len(recs) >= n_recommendations:
                        break

        recommendations[uid] = recs[:n_recommendations]

    return recommendations


if __name__ == "__main__":
    import json
    import os
    import sys
    from pathlib import Path

    # Configure path to sample user_event_history.csv
    base_dir = Path(__file__).resolve().parent.parent
    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))

    data_path = base_dir / "data" / "user_event_history.csv"

    if not data_path.exists():
        data_path = base_dir / "data" / "sample_user_event_history.csv"

    print(f"Loading user event history from: {data_path}")

    # Import data loading pipeline
    try:
        from src.data_processing import load_data

        event_df = load_data(data_path)
    except Exception:
        event_df = pd.read_csv(data_path)

    print("\nDataset Preview:")
    print(event_df.head(10))

    # Compute recommendations
    recommendations_result = recommend_events(event_df, n_recommendations=3)

    print("\n" + "=" * 60)
    print("  PERSONALIZED RECOMMENDATIONS OUTPUT")
    print("=" * 60)
    print(json.dumps(recommendations_result, indent=4))
    print("=" * 60)
