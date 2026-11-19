"""
Recommendation Output Module for BookMyShow Event Ticketing Platform.

Sprint: 1
Ticket: AIML-0011-W1-04
Team: AIML-04
Client: BookMyShow (Fictional)

Provides serialization and export functionality for personalized event
recommendations, formatting recommendations into structured, readable JSON
and persisting them to disk safely with automatic directory creation.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Mapping, Sequence, Union

logger = logging.getLogger(__name__)


def save_recommendations(
    recommendations: Mapping[str, Sequence[str]],
    output_path: Union[str, Path, os.PathLike],
    indent: int = 4,
) -> Path:
    """
    Save the recommendations dictionary to a file in readable JSON format.

    Workflow:
    1. Validates input types: verifies that recommendations is a dictionary/mapping
       and output_path is a valid non-empty string or Path-like object.
    2. Validates that output_path does not point to an existing directory.
    3. Normalizes recommendations to ensure keys are strings and values are lists
       of string event IDs, preserving ordering.
    4. Automatically creates any missing parent directories for output_path.
    5. Serializes the recommendations dictionary to JSON using Python's built-in
       json module with UTF-8 encoding and readable indentation.
    6. Returns the resolved Path to the saved JSON file on success.

    :param recommendations: Dictionary mapping user IDs to lists of recommended event IDs.
                            Example: {"U001": ["E101", "E102"], "U002": ["E103"]}
    :param output_path: Destination path where JSON should be written.
    :param indent: Indentation level for pretty-printing JSON (default: 4).
    :return: Resolved Path of the generated JSON file.
    :raises TypeError: If recommendations is not a mapping or output_path is not a str/Path.
    :raises ValueError: If output_path is empty or invalid.
    :raises IsADirectoryError: If output_path points to an existing directory.
    :raises IOError: If an error occurs during file writing or directory creation.
    """
    # 1. Type validation for recommendations
    if recommendations is None or not isinstance(recommendations, Mapping):
        raise TypeError(
            f"Expected 'recommendations' to be a dict/mapping, got {type(recommendations).__name__}"
        )

    # 2. Type and value validation for output_path
    if output_path is None:
        raise TypeError("output_path cannot be None; expected a valid file path string or Path.")

    if not isinstance(output_path, (str, Path, os.PathLike)):
        raise TypeError(
            f"output_path must be a string or Path-like object, got {type(output_path).__name__}"
        )

    path_str = str(output_path).strip()
    if not path_str:
        raise ValueError("output_path cannot be an empty string.")

    target_path = Path(path_str)

    if target_path.exists() and target_path.is_dir():
        raise IsADirectoryError(
            f"Target path '{output_path}' is an existing directory; expected a file path."
        )

    # 3. Normalize structure (ensure all keys are strings and values are lists of strings)
    formatted_recs: dict[str, list[str]] = {}
    for user_id, events in recommendations.items():
        uid_str = str(user_id)
        if isinstance(events, (list, tuple, set)):
            formatted_recs[uid_str] = [str(e) for e in events]
        else:
            raise TypeError(
                f"Event list for user '{uid_str}' must be a sequence/list, got {type(events).__name__}"
            )

    # 4. Auto-create parent directories if needed
    try:
        parent_dir = target_path.parent
        if parent_dir and not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Created parent directory: %s", parent_dir)
    except Exception as exc:
        raise IOError(f"Failed to create parent directory for '{output_path}': {exc}") from exc

    # 5. Write JSON file using built-in json module with UTF-8 encoding
    try:
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(formatted_recs, f, indent=indent, ensure_ascii=False)
            f.write("\n")  # Ensure clean trailing newline
    except Exception as exc:
        raise IOError(f"Failed to write recommendations JSON to '{output_path}': {exc}") from exc

    logger.info(
        "Successfully saved recommendations for %d users to %s",
        len(formatted_recs),
        target_path,
    )
    return target_path.resolve()
