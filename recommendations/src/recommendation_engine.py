"""
Personalized Event Recommendation Engine for BookMyShow.

Sprint: 1
Ticket: AIML-0011-W1-03
Team: AIML-04
Client: BookMyShow (Fictional)

This module implements a hybrid recommendation engine combining:
1. Popularity-based candidate retrieval (global interaction frequency ranking).
2. Category-based personalization (user interaction history and category affinity).
3. Personalized ranking with exclusion of previously attended events and deduplication.
4. Robust popularity fallback for cold-start and low-history users.
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

    valid_events = data["event_id"].dropna().astype(str).str.strip()
    valid_events = valid_events[valid_events != ""]

    if valid_events.empty:
        return pd.Series(dtype="int64")

    counts = valid_events.value_counts()
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

    cleaned = (
        data[["user_id", "event_id"]]
        .dropna()
        .astype(str)
        .map(str.strip)
    )
    cleaned = cleaned[(cleaned["user_id"] != "") & (cleaned["event_id"] != "")]

    if cleaned.empty:
        return {}

    return {
        uid: set(events)
        for uid, events in cleaned.groupby("user_id")["event_id"]
    }


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

    event_primary_cat: dict[str, str] = (
        cleaned.groupby(["event_id", "event_category"])
        .size()
        .reset_index(name="cnt")
        .sort_values(by=["event_id", "cnt"], ascending=[True, False])
        .drop_duplicates(subset=["event_id"])
        .set_index("event_id")["event_category"]
        .to_dict()
    )

    category_map: dict[str, list[str]] = {}
    for event_id in ranked_popular_events:
        cat = event_primary_cat.get(event_id)
        if cat:
            category_map.setdefault(cat, []).append(event_id)

    return category_map


def apply_popularity_fallback(
    recs: list[str],
    ranked_popular_events: list[str],
    seen: set[str],
    n_recommendations: int,
) -> list[str]:
    """
    Backfill recommendation slots with globally popular events.

    Excludes events the user has already attended and events already recommended,
    ensuring recommendations reach n_recommendations without duplicates.

    :param recs: Existing list of recommended event IDs.
    :param ranked_popular_events: Globally ranked event IDs sorted by popularity descending.
    :param seen: Set of already attended and already recommended event IDs.
    :param n_recommendations: Maximum desired number of recommendations.
    :return: Updated list of recommended event IDs up to n_recommendations.
    """
    if len(recs) >= n_recommendations:
        return recs[:n_recommendations]

    for event in ranked_popular_events:
        if event not in seen:
            recs.append(event)
            seen.add(event)
            if len(recs) >= n_recommendations:
                break

    return recs[:n_recommendations]


def recommend_events(
    data: pd.DataFrame,
    n_recommendations: int = 3,
    user_id: Optional[str] = None,
    **kwargs: Any,
) -> dict[str, list[str]]:
    """
    Recommend relevant events for users using a hybrid recommendation algorithm.

    Algorithm Workflow:
    1. Input Validation:
       - Confirms data is a pandas DataFrame.
       - Safely handles empty DataFrames, missing values, and whitespace.
       - Validates presence of required identifier columns ('user_id', 'event_id').
    2. Global Popularity Ranking:
       - Computes interaction frequency for each event across the dataset.
    3. Category-Based Personalization:
       - For each user, determines preferred categories by interaction volume.
       - Recommends unvisited popular events in those categories.
    4. Popularity-Based Fallback (apply_popularity_fallback):
       - For new/cold-start users, or users who have exhausted category events,
         fills remaining slots with globally popular unvisited events.
    5. Deduplication & Exclusion:
       - Excludes previously attended events and guarantees zero duplicate recommendations.

    :param data: Preprocessed pandas DataFrame with 'user_id', 'event_id', and optional 'event_category'.
    :param n_recommendations: Maximum number of events to recommend per user (default: 3).
    :param user_id: Optional specific user ID to generate recommendations for.
    :param kwargs: Additional optional arguments ('top_n', 'limit', 'n').
    :return: Dictionary mapping user_id string to a list of recommended event_id strings.
    """
    if data is None or not isinstance(data, pd.DataFrame):
        raise TypeError(
            f"Input 'data' must be a pandas DataFrame, got {type(data).__name__}"
        )

    if "top_n" in kwargs:
        n_recommendations = kwargs["top_n"]
    elif "limit" in kwargs:
        n_recommendations = kwargs["limit"]
    elif "n" in kwargs:
        n_recommendations = kwargs["n"]

    n_recommendations = max(0, int(n_recommendations))

    if data.empty:
        return {str(user_id): []} if user_id is not None else {}

    required_cols = {"user_id", "event_id"}
    missing_cols = required_cols - set(data.columns)
    if missing_cols:
        raise ValueError(
            f"Missing required columns in DataFrame: {sorted(list(missing_cols))}. "
            f"Expected at least 'user_id' and 'event_id'."
        )

    cleaned_df = data.dropna(subset=["user_id", "event_id"]).copy()
    cleaned_df["user_id"] = cleaned_df["user_id"].astype(str).str.strip()
    cleaned_df["event_id"] = cleaned_df["event_id"].astype(str).str.strip()
    cleaned_df = cleaned_df[
        (cleaned_df["user_id"] != "") & (cleaned_df["event_id"] != "")
    ]

    if cleaned_df.empty:
        return {str(user_id): []} if user_id is not None else {}

    if n_recommendations == 0:
        target_uids = (
            [str(user_id)]
            if user_id is not None
            else sorted(cleaned_df["user_id"].unique().tolist())
        )
        return {uid: [] for uid in target_uids}

    # Step 1: Global Popularity Ranking
    popularity_series = calculate_event_popularity(cleaned_df)
    ranked_popular_events: list[str] = list(popularity_series.index)

    # Step 2: Category mapping
    has_category = "event_category" in cleaned_df.columns
    category_events_map = (
        get_category_events_map(cleaned_df, ranked_popular_events)
        if has_category
        else {}
    )

    # Step 3: Attended history per user
    user_history = get_user_event_history(cleaned_df)

    # Step 4: Target users
    target_users = (
        [str(user_id).strip()]
        if user_id is not None
        else sorted(cleaned_df["user_id"].unique().tolist())
    )

    recommendations: dict[str, list[str]] = {}

    for uid in target_users:
        attended = user_history.get(uid, set())
        recs: list[str] = []
        seen: set[str] = set(attended)

        # Stage A: Category-Based Personalization
        if has_category and uid in user_history:
            category_affinities = get_user_category_affinities(cleaned_df, uid)
            for category, _ in category_affinities:
                for event in category_events_map.get(category, []):
                    if event not in seen:
                        recs.append(event)
                        seen.add(event)
                        if len(recs) >= n_recommendations:
                            break
                if len(recs) >= n_recommendations:
                    break

        # Stage B: Popularity-Based Fallback
        # Backfill remaining slots with globally popular events
        recs = apply_popularity_fallback(
            recs=recs,
            ranked_popular_events=ranked_popular_events,
            seen=seen,
            n_recommendations=n_recommendations,
        )

        recommendations[uid] = recs

    return recommendations


if __name__ == "__main__":
    import json
    import os
    import sys
    from pathlib import Path

    base_dir = Path(__file__).resolve().parent.parent
    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))

    data_path = base_dir / "data" / "user_event_history.csv"
    if not data_path.exists():
        data_path = base_dir / "data" / "sample_user_event_history.csv"

    try:
        from src.data_processing import load_data

        event_df = load_data(data_path)
    except Exception:
        event_df = pd.read_csv(data_path)

    recs = recommend_events(event_df, n_recommendations=3)
    print(json.dumps(recs, indent=4))
