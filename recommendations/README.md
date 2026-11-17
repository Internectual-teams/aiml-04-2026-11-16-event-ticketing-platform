# BookMyShow Recommendations Service

[![Python Version](https://img.shields.io/badge/python-3.12%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Sprint](https://img.shields.io/badge/sprint-1%20(2026--11--16%20to%202026--11--22)-orange.svg)]()
[![Ticket](https://img.shields.io/badge/ticket-AIML--0011--W1--02-green.svg)]()
[![Team](https://img.shields.io/badge/team-AIML--04-purple.svg)]()

## 1. Project Overview

The **Recommendations Service** is a core sub-service of the **BookMyShow Event Ticketing Platform**. As BookMyShow expands into local events, this service is responsible for analyzing past user behavior, ticket bookings, and event category affinities to generate personalized event recommendations.

### Sprint 1 Objectives & Responsibility
- **Sprint 1, Ticket 1:** `AIML-0011-W1-01` — Virtual environment setup, dependencies, structure, Dockerfile, baseline tests.
- **Sprint 1, Ticket 2:** `AIML-0011-W1-02` — Data loading and preprocessing pipeline for user event interaction data.
- **Assigned Engineer:** Adireddy Devendra (Senior Python / ML Engineer)
- **Role:** Recommendations Service Lead
- **Sprint Goal:** Establish reproducible environment and robust data ingestion/cleaning pipelines for historical user-event interactions without interfering with teammate services (`events_api/`).

---

## 2. Team & Project Details

| Attribute | Details |
|---|---|
| **Project** | BookMyShow Event Ticketing Platform (Fictional MVP) |
| **Team** | AIML-04 |
| **Sprint** | Sprint 1 (2026-11-16 to 2026-11-22) |
| **Current Ticket Key** | `AIML-0011-W1-02` (Data Loading & Preprocessing) |
| **Previous Ticket Key** | `AIML-0011-W1-01` (Environment Setup & Git Setup) |
| **Teammate (Events API)** | Prudhvi Kosuri (`AIML-0010-W1-01`) |
| **Recommendations Lead** | Adireddy Devendra (`AIML-0011-W1-02`) |

---

## 3. Technologies Used

- **Python 3.12 / 3.11**: Core programming language.
- **pandas (>=2.2.0, <3.0.0)**: High-performance data manipulation and analysis for user-event history CSVs.
- **numpy (>=1.26.0, <2.0.0)**: Numerical computing and vectorization for similarity matrix calculations.
- **scikit-learn (>=1.4.0, <1.6.0)**: Machine learning foundation for collaborative filtering, TF-IDF category encoding, and cosine similarity.
- **pytest (>=8.0.0, <9.0.0)**: Automated test discovery and test assertion framework.
- **Docker**: Containerization using `python:3.12-slim` for consistent production deployment.

---

## 4. Folder Structure

The service is strictly encapsulated inside `recommendations/` to ensure zero collision with other services:

```
recommendations/
├── data/
│   ├── .gitkeep                               # Preserves data directory structure
│   └── sample_user_event_history.csv          # Synthetic sample dataset for testing/validation
├── src/
│   ├── __init__.py                            # Module initializer and service version
│   ├── data_processing.py                     # Data loading, validation, and cleaning pipeline
│   └── main.py                                # Service entry point & environment verification
├── tests/
│   ├── test_data_processing.py                # Comprehensive test suite for data loading & cleaning
│   └── test_setup.py                          # Setup & dependency validation test suite
├── .gitignore                                 # Excludes venv, pycache, temporary artifacts
├── Dockerfile                                 # Multi-layer container specification
├── README.md                                  # Service documentation & operations manual
└── requirements.txt                           # Production & test dependencies
```

---

## 5. Environment Setup & Installation

### Step 1: Navigate to the Recommendations Service Directory
Open your terminal at the repository root and change directory to `recommendations/`:
```bash
cd recommendations
```

### Step 2: Virtual Environment Creation
Create a dedicated Python virtual environment named `venv`:

- **Windows (PowerShell or Command Prompt):**
  ```powershell
  python -m venv venv
  # If multiple Python versions are installed:
  py -3.12 -m venv venv
  ```

- **Linux / macOS (Bash / Zsh):**
  ```bash
  python3 -m venv venv
  ```

### Step 3: Virtual Environment Activation

- **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
  *(Note: If execution policies restrict script execution in PowerShell, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` first).*

- **Windows (Command Prompt):**
  ```cmd
  .\venv\Scripts\activate.bat
  ```

- **Linux / macOS:**
  ```bash
  source venv/bin/activate
  ```

Upon activation, your terminal prompt will show `(venv)`.

### Step 4: Install Dependencies
Upgrade pip and install required libraries:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

To deactivate the virtual environment when finished:
```bash
deactivate
```

---

## 6. Data Loading and Preprocessing

### Purpose of `data_processing.py`
The `recommendations/src/data_processing.py` module serves as the foundational data ingestion layer for the Recommendations Service. It ensures that raw user interaction logs from CSV files are properly loaded, schema-validated, type-corrected, cleansed of corrupted or missing records, and formatted into clean pandas DataFrames ready for downstream recommendation algorithms (such as collaborative filtering and content-based event filtering).

### The `load_data(file_path)` Function
The primary interface is `load_data(file_path)`:
```python
def load_data(file_path: Union[str, Path, os.PathLike]) -> pd.DataFrame:
```

### Expected CSV Columns
The incoming dataset must contain the following required columns:
1. `user_id`: Unique identifier for the user.
2. `event_id`: Unique identifier for the event.
3. `timestamp`: Timestamp representing when the user interacted with or booked the event.

*Note: Any additional useful columns (such as `rating`, `category`, `price`) are safely preserved in the resulting DataFrame.*

### Data Type Conversions
- **`user_id`**: Converted to pandas `string` dtype (`StringDtype`), strictly preserving leading zeros and string identifiers (e.g., `'001'` is not converted to integer `1`).
- **`event_id`**: Converted to pandas `string` dtype (`StringDtype`), strictly preserving leading zeros and string identifiers (e.g., `'0101'` remains intact).
- **`timestamp`**: Converted to pandas `datetime64[ns]` using `pd.to_datetime`.

### Missing-Value & Blank Identifier Handling
- Rows with missing (`null`, `NaN`, `pd.NA`) required columns (`user_id`, `event_id`, or `timestamp`) are dropped.
- Whitespace is trimmed from identifier values (`user_id.str.strip()` and `event_id.str.strip()`).
- Empty or whitespace-only identifiers (`""`, `"   "`) are converted to `pd.NA` and discarded.
- Optional metadata columns with null values are retained if the required identifier and timestamp fields are valid.

### Invalid Timestamp Handling
- Timestamps are parsed using `pd.to_datetime(..., errors="coerce")`.
- Unparseable strings, invalid date structures, or out-of-range dates are converted to `pd.NaT` (Not-a-Time).
- Any row with a `pd.NaT` timestamp is dropped safely.
- The DataFrame index is reset (`reset_index(drop=True)`) after row deletion.

### Column Name Normalization
- Column headers are stripped of whitespace and converted to lowercase (e.g., `" USER_ID "` becomes `"user_id"`).
- Normalization prevents duplicate column collisions if identically named columns with different casings exist.

### Error Handling
- **`FileNotFoundError`**: Raised with a descriptive message if the file path does not exist.
- **`EmptyDataError`**: Raised if the CSV file is 0 bytes or has no parseable columns/data.
- **`ValueError`**: Raised if a directory path is passed or if required columns (`user_id`, `event_id`, `timestamp`) are missing.
- **`TypeError`**: Raised if `file_path` is `None` or an invalid non-string/non-path type.

### How to Execute the Function

#### Option 1: Direct Module Execution
Run the script directly from `recommendations/`:
```bash
python src/data_processing.py
```
Or specify a custom CSV path:
```bash
python src/data_processing.py data/sample_user_event_history.csv
```

#### Option 2: Programmatic Usage in Python
```python
from src.data_processing import load_data

df = load_data("data/sample_user_event_history.csv")

print(df.head())
print(df.dtypes)
```

**Expected Output:**
```text
    user_id   event_id           timestamp
0  user_001  event_101 2026-11-15 10:30:00
1  user_002  event_102 2026-11-15 11:45:00
2  user_003  event_103 2026-11-15 14:20:00
3  user_001  event_104 2026-11-16 09:15:00

user_id      string[python]
event_id     string[python]
timestamp    datetime64[ns]
dtype: object
```

---

## 7. Testing Instructions

Automated tests are managed with `pytest`.

### Run All Tests (Setup + Data Processing)
From the `recommendations/` directory:
```bash
pytest
```

### Run Only Data Processing Tests
```bash
pytest -v -s tests/test_data_processing.py
```

### Run Setup & Environment Verification Tests
```bash
pytest -v -s tests/test_setup.py
```

### Expected Test Output
```text
tests/test_data_processing.py::test_load_valid_csv PASSED
tests/test_data_processing.py::test_return_type_is_dataframe PASSED
tests/test_data_processing.py::test_user_id_dtype_and_leading_zeros PASSED
tests/test_data_processing.py::test_event_id_dtype_and_leading_zeros PASSED
tests/test_data_processing.py::test_timestamp_dtype PASSED
tests/test_data_processing.py::test_handling_missing_required_values PASSED
tests/test_data_processing.py::test_handling_invalid_timestamps PASSED
tests/test_data_processing.py::test_removing_blank_identifiers PASSED
tests/test_data_processing.py::test_whitespace_stripped_from_valid_identifiers PASSED
tests/test_data_processing.py::test_missing_required_columns_raises_value_error PASSED
tests/test_data_processing.py::test_nonexistent_file_path_raises_file_not_found PASSED
tests/test_data_processing.py::test_empty_csv_file_raises_empty_data_error PASSED
tests/test_data_processing.py::test_preserving_additional_columns PASSED
tests/test_data_processing.py::test_reset_index_after_cleaning PASSED
tests/test_data_processing.py::test_column_name_normalization PASSED
tests/test_data_processing.py::test_normalize_column_names_duplicate_avoidance PASSED
tests/test_data_processing.py::test_invalid_input_path_types PASSED
tests/test_data_processing.py::test_directory_path_raises_value_error PASSED
tests/test_data_processing.py::test_sample_user_event_history_file_if_present PASSED
tests/test_setup.py::test_pandas_import PASSED
tests/test_setup.py::test_numpy_import PASSED
tests/test_setup.py::test_sklearn_import PASSED
tests/test_setup.py::test_app_module_import PASSED
tests/test_setup.py::test_service_info PASSED
tests/test_setup.py::test_main_execution PASSED
========================== 25 passed in 2.00s ==========================
```

---

## 8. Application Execution

To run the Recommendations Service starter application:

```bash
# Ensure venv is activated
python src/main.py
```

---

## 9. Docker Build and Run Instructions

The service includes a production-ready `Dockerfile` based on `python:3.12-slim` following security and caching best practices (non-root user, multi-stage layer caching).

### Prerequisites
- Docker Engine / Docker Desktop installed and running.

### Build the Docker Image
From the `recommendations/` directory:
```bash
docker build -t bookmyshow-recommendations:latest .
```

Or from the repository root:
```bash
docker build -t bookmyshow-recommendations:latest -f recommendations/Dockerfile recommendations/
```

### Run the Container
```bash
docker run --rm --name bms-recommendations bookmyshow-recommendations:latest
```

### Run Tests Inside Container
```bash
docker run --rm bookmyshow-recommendations:latest pytest -v
```

---

## 10. Service Interface Contract (Team Coordination)

In accordance with the team architectural contract defined in the root `README.md`:

- **Input:** `recommendations/data/user_event_history.csv`
  - Columns: `user_id`, `event_id`, `timestamp`
- **Output:** `recommendations/data/recommendations.json`
  - Format: `{"<user_id>": ["<event_id_1>", "<event_id_2>", ...]}`
- **Core Function Signature:**
  ```python
  def generate_recommendations(history_file_path: str, output_file_path: str) -> None
  ```

---

## 11. Git Workflow & Manual Instructions

All development for this ticket is isolated to the `recommendations/` directory on ticket branch `AIML-0011-W1-02`.

### Step-by-Step Git Commands

1. **Verify Branch:**
   ```bash
   git branch --show-current
   # Output should be: AIML-0011-W1-02
   ```

2. **Stage Only Relevant Recommendations Changes:**
   ```bash
   git add recommendations/src/data_processing.py
   git add recommendations/tests/test_data_processing.py
   git add recommendations/data/sample_user_event_history.csv
   git add recommendations/README.md
   ```

3. **Verify Staged Files:**
   ```bash
   git status
   ```
   Ensure `venv/`, `__pycache__/`, `.pytest_cache/` are **not** staged and only the intended files under `recommendations/` are listed.

4. **Commit Changes:**
   ```bash
   git commit -m "AIML-0011-W1-02: Implement data loading and preprocessing module"
   ```

5. **Push Branch to GitHub:**
   ```bash
   git push origin AIML-0011-W1-02
   ```

6. **Create a Pull Request:**
   - Open GitHub: `https://github.com/Internectual-teams/aiml-04-2026-11-16-event-ticketing-platform`
   - Click **Compare & pull request** for `AIML-0011-W1-02`.
   - Set Base: `main` <- Compare: `AIML-0011-W1-02`.
   - Title: `AIML-0011-W1-02: Implement Data Loading and Preprocessing`
   - Assign teammate for review and link PR in the Internectual workspace.
