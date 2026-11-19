"""
BookMyShow Event Ticketing Platform - Recommendations Service
Team: AIML-04
Sprint: 1 (Ticket: AIML-0011-W1-03)
"""

from src.data_processing import load_data
from src.recommendation_engine import (
    calculate_event_popularity,
    get_user_category_affinities,
    get_user_event_history,
    recommend_events,
)

__version__ = "0.2.0"

__all__ = [
    "load_data",
    "calculate_event_popularity",
    "get_user_category_affinities",
    "get_user_event_history",
    "recommend_events",
]
