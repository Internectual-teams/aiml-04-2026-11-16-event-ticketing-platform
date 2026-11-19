# BookMyShow Recommendations Service

[![Python Version](https://img.shields.io/badge/python-3.12%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Sprint](https://img.shields.io/badge/sprint-1%20(2026--11--16%20to%202026--11--22)-orange.svg)]()
[![Ticket](https://img.shields.io/badge/ticket-AIML--0011--W1--03-green.svg)]()
[![Team](https://img.shields.io/badge/team-AIML--04-purple.svg)]()

## 1. Project Overview

The **Recommendations Service** is a core sub-service of the **BookMyShow Event Ticketing Platform**. As BookMyShow expands into local events, this service is responsible for analyzing past user behavior, ticket bookings, and event category affinities to generate personalized event recommendations.

### Sprint 1 Objectives & Responsibility
- **Sprint 1, Ticket 1:** `AIML-0011-W1-01` — Virtual environment setup, dependencies, structure, Dockerfile, baseline tests.
- **Sprint 1, Ticket 2:** `AIML-0011-W1-02` — Data loading and preprocessing pipeline for user event interaction data.
- **Sprint 1, Ticket 3:** `AIML-0011-W1-03` — Basic recommendation engine (hybrid popularity and category-based personalization).
- **Assigned Engineer:** Adireddy Devendra (Senior Python / ML Engineer)
- **Role:** Recommendations Service Lead
- **Sprint Goal:** Establish reproducible environment, robust data ingestion, and a high-performance personalized recommendation engine for BookMyShow event ticketing.

---

## 2. Team & Project Details

| Attribute | Details |
|---|---|
| **Project** | BookMyShow Event Ticketing Platform (Fictional MVP) |
| **Team** | AIML-04 |
| **Sprint** | Sprint 1 (2026-11-16 to 2026-11-22) |
| **Current Ticket Key** | `AIML-0011-W1-03` (Develop Basic Recommendation Logic) |
| **Previous Ticket Keys** | `AIML-0011-W1-01` (Setup), `AIML-0011-W1-02` (Data Ingestion) |
| **Teammate (Events API)** | Prudhvi Kosuri (`AIML-0010-W1-01`, `AIML-0010-W1-02`) |
| **Recommendations Lead** | Adireddy Devendra (`AIML-0011-W1-03`) |

---

## 3. Technologies Used

- **Python 3.12 / 3.11**: Core programming language.
- **pandas (>=2.2.0, <4.0.0)**: High-performance data manipulation, aggregation, and group-by operations.
- **numpy (>=1.26.0, <3.0.0)**: Numerical computing and vectorization.
- **scikit-learn (>=1.4.0, <2.0.0)**: Machine learning baseline utilities.
- **pytest (>=8.0.0, <10.0.0)**: Automated test discovery, fixtures, and assertions.
- **Docker**: Containerization using `python:3.12-slim` for consistent production deployment.

---

## 4. Folder Structure

The service is strictly encapsulated inside `recommendations/` to ensure zero collision with other services:

```
recommendations/
├── data/
│   ├── .gitkeep                               # Preserves data directory structure
│   ├── sample_user_event_history.csv          # Minimal synthetic dataset (W1-02)
│   ├── user_event_history.csv                 # Comprehensive event history dataset (W1-03)
│   └── recommendations.json                   # Output recommendation dictionary (auto-generated)
├── src/
│   ├── __init__.py                            # Module exports and package version
│   ├── data_processing.py                     # Data loading, validation, and cleaning pipeline
│   ├── recommendation_engine.py               # Hybrid personalized recommendation engine
│   └── main.py                                # Service entry point & pipeline runner
├── tests/
│   ├── test_data_processing.py                # Unit test suite for data loading & cleaning
│   ├── test_recommendation_engine.py          # Unit test suite for recommendation engine
│   └── test_setup.py                          # Setup & dependency validation test suite
├── .gitignore                                 # Excludes venv, pycache, temporary artifacts
├── Dockerfile                                 # Multi-layer container specification
├── README.md                                  # Service documentation & operations manual
└── requirements.txt                           # Production & test dependencies
```

---

## 5. Recommendation Engine Architecture (`recommendation_engine.py`)

### 5.1 What is a Recommendation System?
A recommendation system is an information filtering engine that predicts a user's preference or affinity toward items (such as movies, concerts, or workshops) and suggests items that are most relevant to them. In an event ticketing platform like BookMyShow, recommendation engines boost user engagement, conversion rates, and ticket discovery by matching event catalogs with individual user tastes.

### 5.2 Why This Recommendation Approach Was Selected
For an MVP event ticketing service, a **Hybrid Approach** combining **Popularity-Based Filtering** and **Category-Based Personalization** was selected for several key reasons:
1. **Solves the Cold-Start Problem:** Pure collaborative filtering or deep matrix factorization fails when new users or items with zero/sparse interaction history arrive. Popularity fallback provides high-quality recommendations immediately.
2. **Transparent & Explainable:** Recommendations can be directly explained to users (e.g., *"Because you attended Music concerts"*).
3. **No Heavy External Dependencies or GPU Requirements:** The algorithm relies on vectorized pandas operations without requiring external deep learning frameworks or paid inference APIs.
4. **Deterministic & Testable:** Generates reproducible, consistent rankings ideal for automated verification and CI/CD pipelines.

### 5.3 How Event Popularity is Calculated
Popularity is computed by counting the total interaction frequency of each event across the dataset:
$$\text{Popularity}(e) = \sum_{i \in \text{Interactions}} \mathbb{I}(\text{event\_id}_i = e)$$

In `calculate_event_popularity(data)`:
- Missing, blank, or null event IDs are filtered out.
- Interaction counts are aggregated using pandas `value_counts()`.
- Ties are broken deterministically by sorting primarily by descending frequency and secondarily by ascending event ID.

### 5.4 How Category-Based Personalization Works
In `get_user_category_affinities(data, user_id)`:
1. The engine inspects all events previously attended or interacted with by `user_id`.
2. Each event's category is extracted (e.g., `Music`, `Comedy`, `Theatre`, `Sports`).
3. Category interaction counts are tallied. Categories with higher interaction counts represent stronger user affinity.
4. For candidate generation, popular events belonging to the user's top categories are retrieved first.

### 5.5 How Personalized Ranking Works
The hybrid ranking pipeline prioritizes relevance while maintaining diversity:
1. **Category Affinity Sweep:**
   - Iterate through the user's preferred categories in descending order of interaction count.
   - For each category, inspect constituent events sorted by global popularity.
   - Add events that the user has **not yet attended** and **not yet seen** in the recommendation set.
   - Stop when `n_recommendations` slots are filled.
2. **Popularity-Based Fallback:**
   - If candidate events in preferred categories are exhausted (or if the user has no history or the dataset lacks category metadata), backfill remaining slots from the globally most popular events.
3. **Strict Deduplication:**
   - A tracking set (`seen`) ensures no event ID appears more than once in the user's recommendation list.

### 5.6 How Previously Attended Events Are Excluded
Before generating recommendations for `user_id`:
1. The engine extracts the full set of events the user has previously interacted with:
   $$\text{Attended}(u) = \{ e \mid (u, e) \in \text{Dataset} \}$$
2. The recommendation candidate set initializes `seen = set(Attended(u))`.
3. An event $e$ is appended to recommendations **if and only if** $e \notin seen$.
4. This guarantees:
   $$\text{Recommendations}(u) \cap \text{Attended}(u) = \emptyset$$

### 5.7 The `recommend_events(data)` Function Signature
```python
def recommend_events(
    data: pd.DataFrame,
    n_recommendations: int = 3,
    user_id: Optional[str] = None,
    **kwargs: Any,
) -> dict[str, list[str]]:
```

#### Parameters:
- `data`: Preprocessed pandas DataFrame with at least `user_id` and `event_id` columns.
- `n_recommendations`: Maximum number of events to recommend per user (default: `3`).
- `user_id`: Optional specific user ID. If `None`, returns recommendations for all users.
- `**kwargs`: Supports parameter aliases such as `top_n`, `limit`, or `n`.

#### Return Format:
Returns a dictionary mapping `user_id` to a list of recommended `event_id` strings:
```json
{
    "U001": ["E103", "E115", "E116"],
    "U002": ["E109", "E101", "E102"],
    "U003": ["E101", "E102", "E111"]
}
```

---

## 6. Dataset Specification (`user_event_history.csv`)

The production sample dataset is located at `recommendations/data/user_event_history.csv`.

### Columns:
- `user_id`: Unique identifier for the user (e.g., `U001`, `U002`).
- `event_id`: Unique identifier for the event (e.g., `E101`, `E102`).
- `event_category`: Category of the event (`Music`, `Comedy`, `Theatre`, `Dance`, `Sports`, `Tech`).
- `interaction_type`: Action performed (`book`, `attend`, `view`, `like`, `click`).
- `timestamp`: Timestamp of the interaction (e.g., `2026-11-10 10:15:00`).

### Sample Input Data:
```csv
user_id,event_id,event_category,interaction_type,timestamp
U001,E101,Music,book,2026-11-10 10:15:00
U001,E101,Music,attend,2026-11-10 19:30:00
U001,E102,Music,view,2026-11-11 11:00:00
U001,E102,Music,book,2026-11-11 14:20:00
U001,E107,Comedy,like,2026-11-12 16:45:00
U002,E104,Theatre,book,2026-11-10 09:00:00
U002,E104,Theatre,attend,2026-11-10 18:00:00
U002,E105,Theatre,view,2026-11-12 12:30:00
U002,E110,Dance,book,2026-11-13 15:10:00
```

### Actual Output Generated:
```json
{
    "U001": ["E103", "E115", "E116"],
    "U002": ["E109", "E101", "E102"],
    "U003": ["E101", "E102", "E111"],
    "U004": ["E101", "E102", "E106"],
    "U005": ["E101", "E102", "E106"],
    "U006": ["E107", "E108", "E102"],
    "U007": ["E102", "E103", "E115"],
    "U008": ["E115", "E116", "E107"],
    "U009": ["E110", "E112", "E114"],
    "U010": ["E106", "E111", "E104"]
}
```

---

## 7. Execution Instructions

### Option 1: Execute Recommendation Engine Independently
From `recommendations/`:
```bash
python src/recommendation_engine.py
```
Or from the project repository root:
```bash
python recommendations/src/recommendation_engine.py
```

### Option 2: Run via the Main Service Entry Point
Runs environment checks, ingests data, and writes `recommendations.json`:
```bash
python recommendations/src/main.py
```

### Option 3: Programmatic API Usage in Python
```python
from src.data_processing import load_data
from src.recommendation_engine import recommend_events

# 1. Load preprocessed interaction data
df = load_data("data/user_event_history.csv")

# 2. Generate recommendations for all users (top 3)
all_recs = recommend_events(df, n_recommendations=3)
print(all_recs["U001"])  # Output: ['E103', 'E115', 'E116']

# 3. Generate recommendations for a specific user
single_rec = recommend_events(df, n_recommendations=5, user_id="U002")
print(single_rec)
```

---

## 8. Testing Instructions

Automated test execution with `pytest`.

### Run All Test Suites (41 Tests)
```bash
# From repository root
pytest recommendations/tests

# Or from recommendations/ directory
cd recommendations
pytest tests
```

### Run Only Recommendation Engine Tests
```bash
pytest -v recommendations/tests/test_recommendation_engine.py
```

### Run Data Ingestion & Preprocessing Tests
```bash
pytest -v recommendations/tests/test_data_processing.py
```

### Run Setup Tests
```bash
pytest -v recommendations/tests/test_setup.py
```

### Test Suite Summary:
| Test Suite | Scenarios Covered | Tests | Status |
|---|---|:---:|:---:|
| `test_recommendation_engine.py` | Normal generation, personalization, fallback, attended exclusion, deduplication, empty DFs, NaNs, cold start, configurable top-N | 16 | **PASSING** |
| `test_data_processing.py` | CSV loading, type casting, schema validation, string trimming, null timestamps, invalid paths | 19 | **PASSING** |
| `test_setup.py` | Imports, service info, dependency validation, main entry point | 6 | **PASSING** |
| **Total** | **All core functionality and edge cases verified** | **41** | **ALL PASS** |

---

## 9. Docker Instructions

### Build Docker Image
```bash
docker build -t bookmyshow-recommendations:latest recommendations/
```

### Run Containerized Application
```bash
docker run --rm bookmyshow-recommendations:latest
```

### Run Test Suite in Container
```bash
docker run --rm bookmyshow-recommendations:latest pytest tests/
```

---

## 10. Git Workflow & Remote Submission

All work for this ticket is isolated to the `recommendations/` directory on ticket branch `AIML-0011-W1-03`.

### Git Commands Executed:
1. **Branch Verification:**
   ```bash
   git checkout -B AIML-0011-W1-03 origin/AIML-0011-W1-02
   ```
2. **Stage Ticket Files:**
   ```bash
   git add recommendations/src/recommendation_engine.py
   git add recommendations/src/main.py
   git add recommendations/src/__init__.py
   git add recommendations/data/user_event_history.csv
   git add recommendations/tests/test_recommendation_engine.py
   git add recommendations/.gitignore
   git add recommendations/README.md
   ```
3. **Commit Changes:**
   ```bash
   git commit -m "feat(recommendations): implement personalized event recommendation logic"
   ```
4. **Push Branch to Remote:**
   ```bash
   git push origin AIML-0011-W1-03
   ```
