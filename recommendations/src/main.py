"""
BookMyShow Event Ticketing Platform - Recommendations Service
Team: AIML-04
Ticket: AIML-0011-W1-03
Sprint: 1

Main application demonstrating environment setup, dependency verification,
and pipeline execution for the BookMyShow Recommendations Service.
"""

import json
import os
from pathlib import Path
import sys
from typing import Optional

# Ensure recommendations root directory is on sys.path for direct execution
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import numpy as np
import pandas as pd
import sklearn

from src.data_processing import load_data
from src.recommendation_engine import recommend_events


def get_service_info() -> dict[str, str]:
    """Retrieve service metadata and installed library versions."""
    return {
        "service_name": "BookMyShow Recommendations Service",
        "python_version": sys.version.split()[0],
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
        "sklearn_version": sklearn.__version__,
    }


def generate_recommendations(
    history_file_path: str,
    output_file_path: str,
    n_recommendations: int = 3,
) -> None:
    """
    Generate event recommendations for users based on historical interaction data
    and persist results to a JSON file.

    Workflow:
    1. Ingests and cleans user interaction data via load_data().
    2. Executes hybrid personalized recommendation engine via recommend_events().
    3. Serializes recommendation dictionary to output JSON file.

    :param history_file_path: Path to user_event_history.csv
    :param output_file_path: Path to output recommendations.json
    :param n_recommendations: Number of recommendations per user (default: 3).
    """
    print(f"Reading user event history from: {history_file_path}")
    data = load_data(history_file_path)
    print(f"Loaded {len(data)} valid interaction records across {data['user_id'].nunique()} users.")

    recommendations = recommend_events(data, n_recommendations=n_recommendations)

    out_path = Path(output_file_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(recommendations, f, indent=4)

    print(f"Recommendations successfully generated and written to: {output_file_path}")


def main() -> int:
    """Main application entry point."""
    info = get_service_info()

    print("=" * 60)
    print(f"  {info['service_name']}")
    print("  Team: AIML-04 | Ticket: AIML-0011-W1-03 | Sprint: 1")
    print("=" * 60)
    print("Environment & Dependency Verification:")
    print(f"  - Python:       {info['python_version']}")
    print(f"  - pandas:       {info['pandas_version']}")
    print(f"  - numpy:        {info['numpy_version']}")
    print(f"  - scikit-learn: {info['sklearn_version']}")
    print("=" * 60)

    # If default dataset exists, generate sample recommendations
    base_dir = Path(__file__).resolve().parent.parent
    history_file = base_dir / "data" / "user_event_history.csv"
    output_file = base_dir / "data" / "recommendations.json"

    if history_file.exists():
        print(f"\nTriggering automated recommendation generation on {history_file.name}...")
        generate_recommendations(str(history_file), str(output_file))
        print("Status: Service environment and recommendations pipeline initialized successfully.")
    else:
        print("Status: Service environment initialized successfully.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
