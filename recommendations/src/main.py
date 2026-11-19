"""
BookMyShow Event Ticketing Platform - Recommendations Service
Team: AIML-04
Ticket: AIML-0011-W1-04
Sprint: 1

Main execution script orchestrating the end-to-end recommendation workflow:
1. Validates and loads user event history data.
2. Performs data preprocessing and schema validation.
3. Computes personalized event recommendations using the recommendation engine.
4. Serializes and exports recommendations to formatted JSON.
5. Provides command-line interface and standalone execution capabilities.
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
import sys
from typing import Any, Optional, Union

# Ensure recommendations root and src directory are on sys.path for direct execution
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import numpy as np
import pandas as pd
import sklearn

from src.data_processing import REQUIRED_COLUMNS, load_data
from src.recommendation_engine import recommend_events
from src.recommendation_output import save_recommendations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("recommendations.main")


def get_service_info() -> dict[str, str]:
    """Retrieve service metadata and installed library versions."""
    return {
        "service_name": "BookMyShow Recommendations Service",
        "ticket": "AIML-0011-W1-04",
        "team": "AIML-04",
        "sprint": "1",
        "python_version": sys.version.split()[0],
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
        "sklearn_version": sklearn.__version__,
    }


def validate_dataset_path(file_path: Union[str, Path]) -> Path:
    """
    Validate that the specified dataset path exists, is a file, and is non-empty.

    :param file_path: Path to the dataset CSV file.
    :return: Resolved Path object.
    :raises FileNotFoundError: If the file does not exist.
    :raises ValueError: If the path is a directory or file is empty.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input dataset not found at: '{path.resolve()}'")
    if path.is_dir():
        raise ValueError(f"Expected a CSV file path, but received a directory: '{path.resolve()}'")
    if path.stat().st_size == 0:
        raise ValueError(f"Input dataset at '{path.resolve()}' is empty (0 bytes).")
    return path.resolve()


def generate_recommendations(
    history_file_path: Union[str, Path],
    output_file_path: Union[str, Path],
    n_recommendations: int = 3,
) -> dict[str, list[str]]:
    """
    Orchestrate the end-to-end recommendation generation workflow.

    Steps:
    1. Validate input dataset existence and integrity.
    2. Load and preprocess user event history using the data processing module.
    3. Validate required columns ('user_id', 'event_id', 'timestamp').
    4. Execute the hybrid personalized recommendation engine.
    5. Save the generated recommendations dictionary to JSON using recommendation_output.
    6. Return the recommendation results.

    :param history_file_path: Path to user_event_history.csv.
    :param output_file_path: Destination path for recommendations.json.
    :param n_recommendations: Number of event recommendations per user (default: 3).
    :return: Generated recommendations dictionary.
    """
    print(f"\n[Step 1/4] Validating and loading user event history from: {history_file_path}")
    validated_csv_path = validate_dataset_path(history_file_path)

    # Preprocess and validate dataset schema
    data = load_data(validated_csv_path)
    total_records = len(data)
    unique_users = data["user_id"].nunique()
    unique_events = data["event_id"].nunique()
    print(
        f"  --> Successfully loaded and cleaned {total_records} interaction records "
        f"({unique_users} unique users, {unique_events} unique events)."
    )

    # Step 2: Validate required columns presence
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in data.columns]
    if missing_cols:
        raise ValueError(
            f"Dataset is missing required columns: {missing_cols}. Expected {REQUIRED_COLUMNS}."
        )

    # Step 3: Generate recommendations
    print(f"\n[Step 2/4] Executing hybrid recommendation engine (top {n_recommendations} per user)...")
    recommendations = recommend_events(data, n_recommendations=n_recommendations)
    print(f"  --> Generated recommendations for {len(recommendations)} active users.")

    # Step 4: Save recommendations to JSON
    print(f"\n[Step 3/4] Serializing and persisting recommendations to: {output_file_path}")
    saved_path = save_recommendations(recommendations, output_file_path)
    print(f"  --> Recommendations successfully written to: {saved_path}")

    # Step 5: Summary preview
    print("\n[Step 4/4] Recommendations Summary Preview:")
    print("  +-----------------+----------------------------------------+")
    print("  | User ID         | Recommended Event IDs                  |")
    print("  +-----------------+----------------------------------------+")
    for uid, rec_events in sorted(recommendations.items())[:10]:
        recs_str = ", ".join(rec_events) if rec_events else "(No recommendations)"
        print(f"  | {uid:<15} | {recs_str:<38} |")
    if len(recommendations) > 10:
        print(f"  | ... and {len(recommendations) - 10} more users |")
    print("  +-----------------+----------------------------------------+")

    return recommendations


def parse_arguments(args: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments for main execution."""
    parser = argparse.ArgumentParser(
        description="BookMyShow Event Ticketing Platform - Recommendations Service",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input",
        "-i",
        dest="input_file",
        type=str,
        default=str(BASE_DIR / "data" / "user_event_history.csv"),
        help="Path to the input user event history CSV dataset.",
    )
    parser.add_argument(
        "--output",
        "-o",
        dest="output_file",
        type=str,
        default=str(BASE_DIR / "data" / "recommendations.json"),
        help="Path to the destination JSON recommendations file.",
    )
    parser.add_argument(
        "--num-recommendations",
        "-n",
        dest="n_recommendations",
        type=int,
        default=3,
        help="Number of recommendations to generate per user.",
    )
    # If args is None, pass empty list so callers of main() without args don't inherit sys.argv
    return parser.parse_args(args if args is not None else [])


def main(argv: Optional[list[str]] = None) -> int:
    """
    Main application entry point.

    :param argv: Optional command-line argument list.
    :return: Exit status code (0 for success, non-zero for failure).
    """
    args = parse_arguments(argv)
    info = get_service_info()

    print("=" * 70)
    print(f"  {info['service_name']}")
    print(f"  Team: {info['team']} | Ticket: {info['ticket']} | Sprint: {info['sprint']}")
    print("=" * 70)
    print("Environment & Dependency Verification:")
    print(f"  - Python:       {info['python_version']}")
    print(f"  - pandas:       {info['pandas_version']}")
    print(f"  - numpy:        {info['numpy_version']}")
    print(f"  - scikit-learn: {info['sklearn_version']}")
    print("=" * 70)

    input_path = Path(args.input_file)
    output_path = Path(args.output_file)

    # Validate existence of input dataset
    if not input_path.exists():
        logger.error(
            "Dataset file not found at: '%s'. Aborting execution.",
            input_path.resolve(),
        )
        print(
            f"\n[ERROR] Input dataset not found: {input_path.resolve()}\n"
            f"Please ensure '{input_path}' exists before running.",
            file=sys.stderr,
        )
        return 1

    try:
        generate_recommendations(
            history_file_path=input_path,
            output_file_path=output_path,
            n_recommendations=args.n_recommendations,
        )
        print("\n[SUCCESS] Recommendation pipeline completed successfully.")
        return 0
    except Exception as exc:
        logger.exception("Recommendation pipeline execution failed: %s", exc)
        print(f"\n[EXECUTION ERROR] Pipeline failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
