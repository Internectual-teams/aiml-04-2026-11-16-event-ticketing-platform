"""
Setup and environment validation tests for Recommendations Service.
Ticket: AIML-0011-W1-01
Team: AIML-04
Sprint: 1
"""

import importlib
import sys
from pathlib import Path

# Ensure 'src' and 'recommendations' root directory are available on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def test_pandas_import():
    """Verify pandas imports successfully and has a valid version."""
    import pandas as pd

    assert pd is not None
    assert hasattr(pd, "__version__")
    assert isinstance(pd.__version__, str)


def test_numpy_import():
    """Verify numpy imports successfully and has a valid version."""
    import numpy as np

    assert np is not None
    assert hasattr(np, "__version__")
    assert isinstance(np.__version__, str)


def test_sklearn_import():
    """Verify scikit-learn imports successfully and has a valid version."""
    import sklearn

    assert sklearn is not None
    assert hasattr(sklearn, "__version__")
    assert isinstance(sklearn.__version__, str)


def test_app_module_import():
    """Verify the recommendations application module can be imported."""
    src_main = importlib.import_module("src.main")
    assert src_main is not None
    assert hasattr(src_main, "main")
    assert hasattr(src_main, "get_service_info")
    assert callable(src_main.main)


def test_service_info():
    """Verify service info returns expected keys and correct service name."""
    from src.main import get_service_info

    info = get_service_info()
    assert isinstance(info, dict)
    assert info["service_name"] == "BookMyShow Recommendations Service"
    assert "pandas_version" in info
    assert "numpy_version" in info
    assert "sklearn_version" in info
    assert "python_version" in info


def test_main_execution():
    """Verify main() function executes cleanly returning exit code 0."""
    from src.main import main

    exit_code = main()
    assert exit_code == 0
