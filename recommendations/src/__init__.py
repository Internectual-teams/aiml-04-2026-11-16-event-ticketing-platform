"""
BookMyShow Event Ticketing Platform - Recommendations Service
Team: AIML-04
Sprint: 1 (Ticket: AIML-0011-W1-04)
"""

from src.data_processing import load_data
from src.recommendation_engine import (
    apply_popularity_fallback,
    calculate_event_popularity,
    get_category_events_map,
    get_user_category_affinities,
    get_user_event_history,
    recommend_events,
)
from src.recommendation_output import save_recommendations

__version__ = "0.3.0"

__all__ = [
    "load_data",
    "apply_popularity_fallback",
    "calculate_event_popularity",
    "get_category_events_map",
    "get_user_category_affinities",
    "get_user_event_history",
    "recommend_events",
    "save_recommendations",
]
