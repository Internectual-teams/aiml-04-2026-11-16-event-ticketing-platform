# BookMyShow Recommendations Service

[![Python Version](https://img.shields.io/badge/python-3.12%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Sprint](https://img.shields.io/badge/sprint-1%20(2026--11--16%20to%202026--11--22)-orange.svg)]()
[![Ticket](https://img.shields.io/badge/ticket-AIML--0011--W1--04-green.svg)](https://github.com/Internectual-teams/aiml-04-2026-11-16-event-ticketing-platform)
[![Team](https://img.shields.io/badge/team-AIML--04-purple.svg)]()
[![Build & Test](https://img.shields.io/badge/tests-59%20passed-brightgreen.svg)]()

## 1. Project Overview

The **Recommendations Service** is a core component of the **BookMyShow Event Ticketing Platform**. As BookMyShow expands into local events, workshops, concerts, and cultural performances, this service is responsible for ingesting historical user interaction data, calculating personalized recommendations, and serializing the output into standard formats consumable by downstream services (such as the Events API Backend, web clients, and mobile applications).

### Sprint 1 Roadmap & Tickets
- **Ticket 1 (`AIML-0011-W1-01`):** Service architecture setup, dependency configuration, Docker containerization, and baseline health tests.
- **Ticket 2 (`AIML-0011-W1-02`):** Data loading, validation, schema normalization, and cleaning pipeline (`data_processing.py`).
- **Ticket 3 (`AIML-0011-W1-03`):** Hybrid personalized recommendation engine (`recommendation_engine.py`) with popularity ranking, category affinity matching, attended-event exclusion, and cold-start fallback.
- **Ticket 4 (`AIML-0011-W1-04` - CURRENT):** Recommendation output serialization (`recommendation_output.py`), end-to-end orchestration pipeline (`main.py`), production Docker deployment, and integration test suite (`test_recommendation_output.py`).

**Assigned Lead Engineer:** Adireddy Devendra (Senior Python / Machine Learning Engineer)  
**Assigned Module:** Recommendations Service  

---

## 2. Team & Project Details

| Attribute | Details |
|---|---|
| **Client** | BookMyShow (Fictional) |
| **Project** | Event Ticketing Platform (MVP) |
| **Team** | AIML-04 |
| **Sprint** | Sprint 1 (2026-11-16 to 2026-11-22) |
| **Current Ticket Key** | `AIML-0011-W1-04` (Create Recommendation Output and Main Script) |
| **Previous Ticket Keys** | `AIML-0011-W1-01` (Setup), `AIML-0011-W1-02` (Ingestion), `AIML-0011-W1-03` (Engine Logic) |
| **Teammate (Events API)** | Prudhvi Kosuri (`AIML-0010-W1-01`, `AIML-0010-W1-02`) |
| **Recommendations Lead** | Adireddy Devendra (`AIML-0011-W1-04`) |

---

## 3. Technologies Used

- **Python 3.12 / 3.11**: Primary language environment.
- **json (Python Standard Library)**: Native, high-performance, specification-compliant JSON serialization with UTF-8 encoding.
- **pandas (>=2.2.0, <4.0.0)**: Data loading, schema validation, and vector manipulations.
- **numpy (>=1.26.0, <3.0.0)**: Array operations and ranking support.
- **scikit-learn (>=1.4.0, <2.0.0)**: Machine learning baseline utilities.
- **pytest (>=8.0.0, <10.0.0)**: Automated test suite, fixtures, parameterization, and mock testing.
- **Docker**: Containerization using `python:3.12-slim` for reproducible cross-platform deployments.

---

## 4. Folder Structure

The service is strictly encapsulated inside `recommendations/` to preserve separation of concerns and avoid collisions with other microservices:

```
recommendations/
├── data/
│   ├── .gitkeep                               # Preserves empty data directory structure
│   ├── sample_user_event_history.csv          # Minimal synthetic dataset (W1-02)
│   ├── user_event_history.csv                 # Production sample event history dataset (W1-03)
│   └── recommendations.json                   # Output recommendation dictionary (W1-04 generated)
├── src/
│   ├── __init__.py                            # Module exports and package version
│   ├── data_processing.py                     # Data loading, validation, and cleaning pipeline
│   ├── recommendation_engine.py               # Hybrid personalized recommendation engine
│   ├── recommendation_output.py               # JSON serialization and output persistence (W1-04)
│   └── main.py                                # End-to-end service orchestration entry point (W1-04)
├── tests/
│   ├── test_data_processing.py                # Unit test suite for data loading & cleaning (19 tests)
│   ├── test_recommendation_engine.py          # Unit test suite for recommendation engine (16 tests)
│   ├── test_recommendation_output.py          # Unit & integration tests for output and main (18 tests)
│   └── test_setup.py                          # Setup & dependency validation test suite (6 tests)
├── .gitignore                                 # Excludes venv, pycache, temporary artifacts
├── Dockerfile                                 # Multi-stage production container specification
├── README.md                                  # Service documentation & operations manual
└── requirements.txt                           # Production & test dependencies
```

---

## 5. Recommendation Output Generation (`recommendation_output.py`)

### 5.1 Purpose of Recommendation Output Generation
In a decoupled microservices architecture, the recommendation engine computes mathematical affinities and candidate sets in memory. However, to be consumed by:
1. Downstream backend services (e.g., the Events API backend).
2. Asynchronous cache warmup jobs (Redis, Memcached).
3. Client-facing mobile and web user interfaces.
4. Analytics and auditing pipelines.

The in-memory recommendations dictionary must be serialized into a structured, persistent, and universally interoperable format.

### 5.2 Why JSON Was Selected as the Output Format
- **Language Agnostic Interoperability:** JSON (JavaScript Object Notation) is the ubiquitous standard for REST APIs, message brokers, and web clients.
- **Direct Mapping to Key-Value Entities:** A JSON object directly mirrors a mapping of `user_id` -> `list[event_id]`, preserving constant-time $O(1)$ lookups for downstream user queries.
- **Human Readability & Debuggability:** Formatted JSON with indentation can be directly reviewed by engineers, QA testers, and operations teams without specialized viewers.
- **Native Language Support:** Python's built-in `json` module offers zero third-party dependencies, safe Unicode handling (`UTF-8`), and deterministic output structure.

### 5.3 Function Specification: `save_recommendations()`

```python
def save_recommendations(
    recommendations: Mapping[str, Sequence[str]],
    output_path: Union[str, Path, os.PathLike],
    indent: int = 4,
) -> Path:
```

#### How It Works:
1. **Type & Value Validation:** Checks that `recommendations` is a dictionary/mapping and `output_path` is a non-empty string or Path object. Rejects directories and non-sequence values with clear exceptions (`TypeError`, `ValueError`, `IsADirectoryError`).
2. **Key and Value Normalization:** Preserves user ID strings and converts any sequence of event IDs (lists, tuples, sets) into standard lists of strings.
3. **Automatic Directory Creation:** Inspects `target_path.parent` and automatically creates all non-existent directories using `parent_dir.mkdir(parents=True, exist_ok=True)`.
4. **UTF-8 Serialization:** Employs `json.dump()` with `indent=4` and `ensure_ascii=False` under UTF-8 encoding, guaranteeing proper representation of international characters and symbols.
5. **Safe Error Handling:** Wraps file I/O operations and raises descriptive `IOError` on OS-level write failures.
6. **Return Value:** Returns the resolved `Path` to the generated JSON file for seamless chaining.

#### Example Input:
```python
{
    "U001": ["E101", "E102"],
    "U002": ["E103", "E104"]
}
```

#### Expected JSON Output:
```json
{
    "U001": [
        "E101",
        "E102"
    ],
    "U002": [
        "E103",
        "E104"
    ]
}
```

---

## 6. End-to-End Workflow & Main Script (`src/main.py`)

### 6.1 Architectural Workflow
The recommendation pipeline executes the following sequence:

```
+------------------------------------------+
| CSV Dataset                              |
| (data/user_event_history.csv)            |
+------------------------------------------+
                     |
                     v
+------------------------------------------+
| Ingestion & Schema Validation            |
| (src/data_processing.load_data)          |
+------------------------------------------+
                     |
                     v
+------------------------------------------+
| Hybrid Recommendation Engine             |
| (src/recommendation_engine)              |
| - Calculate Popularity                   |
| - Filter Attended Events                 |
| - Match Category Affinities              |
| - Backfill Cold-Start Candidates         |
+------------------------------------------+
                     |
                     v
+------------------------------------------+
| JSON Serialization & Export              |
| (src/recommendation_output)              |
| - UTF-8 Encoding                         |
| - Auto Parent Directory Creation         |
+------------------------------------------+
                     |
                     v
+------------------------------------------+
| Output JSON File                         |
| (data/recommendations.json)              |
+------------------------------------------+
```

### 6.2 How `main.py` Orchestrates the Process
1. **Environment & Dependency Verification:** Inspects Python runtime and installed package versions via `get_service_info()`.
2. **Path Resolution:** Uses `pathlib.Path` relative to file origin (`BASE_DIR = Path(__file__).resolve().parent.parent`) to ensure execution succeeds regardless of working directory.
3. **Argument Parsing:** Accepts optional CLI flags (`--input`, `--output`, `--num-recommendations`).
4. **Data Validation:** Ensures input CSV exists and contains the mandatory columns (`user_id`, `event_id`, `timestamp`).
5. **Preprocessing:** Cleans identifiers, trims whitespace, handles null values, and parses timestamps via `load_data()`.
6. **Recommendation Generation:** Calls `recommend_events(data, n_recommendations=3)`.
7. **JSON Persistence:** Calls `save_recommendations(recs, output_file)` to write formatted JSON.
8. **Summary Reporting:** Prints a structured preview table of generated user recommendations and exits with status code `0`.

---

## 7. Dataset Specifications & Locations

### 7.1 Input Dataset Location
- **Path:** `recommendations/data/user_event_history.csv`
- **Fallback / Minimal Sample:** `recommendations/data/sample_user_event_history.csv`
- **Schema:**
  - `user_id` (string): Unique user identifier (e.g., `U001`, `U002`).
  - `event_id` (string): Unique event identifier (e.g., `E101`, `E102`).
  - `event_category` (string): Category tag (`Music`, `Comedy`, `Theatre`, `Dance`, `Sports`, `Tech`).
  - `interaction_type` (string): Action type (`book`, `attend`, `view`, `like`).
  - `timestamp` (datetime): Interaction timestamp (`YYYY-MM-DD HH:MM:SS`).

### 7.2 Output JSON Location
- **Path:** `recommendations/data/recommendations.json`
- **Format:** Formatted JSON mapping each `user_id` to an ordered list of `event_id` strings.

### 7.3 Actual Output Generated (`recommendations.json`)
```json
{
    "U001": [
        "E103",
        "E115",
        "E116"
    ],
    "U002": [
        "E109",
        "E101",
        "E102"
    ],
    "U003": [
        "E101",
        "E102",
        "E111"
    ],
    "U004": [
        "E101",
        "E102",
        "E106"
    ],
    "U005": [
        "E101",
        "E102",
        "E106"
    ],
    "U006": [
        "E107",
        "E108",
        "E102"
    ],
    "U007": [
        "E102",
        "E103",
        "E115"
    ],
    "U008": [
        "E115",
        "E116",
        "E107"
    ],
    "U009": [
        "E110",
        "E112",
        "E114"
    ],
    "U010": [
        "E106",
        "E111",
        "E104"
    ]
}
```

---

## 8. Execution Instructions

### 8.1 Execute as a Python Module (Recommended)
From the `recommendations/` directory:
```bash
python -m src.main
```

### 8.2 Direct Execution via Script Path
From the `recommendations/` directory:
```bash
python src/main.py
```

Or from the repository root:
```bash
python recommendations/src/main.py
```

### 8.3 CLI Arguments Customization
You can pass custom input/output paths or specify the number of recommendations:
```bash
python -m src.main --input data/user_event_history.csv --output data/recommendations.json -n 5
```

---

## 9. Automated Testing Instructions

The test suite contains **59 automated tests** covering data processing, recommendation heuristics, JSON output formatting, error handling, and end-to-end CLI workflows.

### 9.1 Run All Tests
From the `recommendations/` directory:
```bash
pytest -v
```
Or from the project root:
```bash
pytest -v recommendations/tests/
```

### 9.2 Run Specific Test Suites
```bash
# Recommendation Output & Main Workflow tests (Ticket W1-04)
pytest -v tests/test_recommendation_output.py

# Recommendation Engine tests (Ticket W1-03)
pytest -v tests/test_recommendation_engine.py

# Data Processing tests (Ticket W1-02)
pytest -v tests/test_data_processing.py

# Environment & Setup tests (Ticket W1-01)
pytest -v tests/test_setup.py
```

### Test Suite Summary:
| Test Suite | Scenarios Covered | Tests | Status |
|---|---|:---:|:---:|
| `test_recommendation_output.py` | JSON formatting, file creation, UTF-8, type validation, auto parent dir, CLI workflow, error handling | 18 | **PASSING** |
| `test_recommendation_engine.py` | Hybrid personalization, popularity, attended exclusion, deduplication, cold start | 16 | **PASSING** |
| `test_data_processing.py` | CSV loading, type casting, schema validation, string trimming, null timestamps | 19 | **PASSING** |
| `test_setup.py` | Imports, service info, dependency validation, main entry point | 6 | **PASSING** |
| **Total** | **Comprehensive service coverage and backward compatibility** | **59** | **ALL PASS** |

---

## 10. Docker Instructions

The containerized service uses `python:3.12-slim` and executes with a non-root application user (`appuser:1001`).

### 10.1 Build the Docker Image
From the `recommendations/` directory:
```bash
docker build -t bookmyshow-recommendations .
```

Or from the repository root:
```bash
docker build -t bookmyshow-recommendations recommendations/
```

### 10.2 Run the Docker Container (Default Execution)
```bash
docker run --rm bookmyshow-recommendations
```

### 10.3 Run with Host Volume Mount (Persist `recommendations.json` to Host)
To access the generated `recommendations.json` directly on the host machine:
```bash
# On Linux / macOS / PowerShell (inside recommendations/):
docker run --rm -v "${PWD}/data:/app/data" bookmyshow-recommendations

# On Windows Command Prompt (inside recommendations/):
docker run --rm -v "%cd%/data:/app/data" bookmyshow-recommendations
```

### 10.4 Run the Test Suite Inside Docker
```bash
docker run --rm bookmyshow-recommendations pytest tests/ -v
```

---

## 11. Git Workflow & Ticket Submission

All work for this ticket is completed on ticket branch `AIML-0011-W1-04`.

### Commands Executed:
1. **Branch Checkout:**
   ```bash
   git checkout -b AIML-0011-W1-04
   ```
2. **Stage Ticket Files:**
   ```bash
   git add recommendations/src/recommendation_output.py
   git add recommendations/src/main.py
   git add recommendations/src/__init__.py
   git add recommendations/tests/test_recommendation_output.py
   git add recommendations/data/recommendations.json
   git add recommendations/Dockerfile
   git add recommendations/.gitignore
   git add recommendations/README.md
   ```
3. **Commit Changes:**
   ```bash
   git commit -m "feat(recommendations): add JSON output and main execution script"
   ```
4. **Push Branch to Origin:**
   ```bash
   git push origin AIML-0011-W1-04
   ```
