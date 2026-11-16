# BookMyShow Recommendations Service

[![Python Version](https://img.shields.io/badge/python-3.12%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Sprint](https://img.shields.io/badge/sprint-1%20(2026--11--16%20to%202026--11--22)-orange.svg)]()
[![Ticket](https://img.shields.io/badge/ticket-AIML--0011--W1--01-green.svg)]()
[![Team](https://img.shields.io/badge/team-AIML--04-purple.svg)]()

## 1. Project Overview

The **Recommendations Service** is a core sub-service of the **BookMyShow Event Ticketing Platform**. As BookMyShow expands into local events, this service is responsible for analyzing past user behavior, ticket bookings, and event category affinities to generate personalized event recommendations.

### Sprint 1 Objective & Responsibility
- **Ticket ID:** `AIML-0011-W1-01`
- **Assigned Engineer:** Adireddy Devendra (Senior Python / ML Engineer)
- **Role:** Recommendations Service Lead
- **Sprint Goal:** Establish a reproducible Python virtual environment, package dependencies, clean project architecture, testing harness with `pytest`, containerization via Dockerfile, and Git workflow without interfering with teammate services (`events_api/`).

---

## 2. Team & Project Details

| Attribute | Details |
|---|---|
| **Project** | BookMyShow Event Ticketing Platform (Fictional MVP) |
| **Team** | AIML-04 |
| **Sprint** | Sprint 1 (2026-11-16 to 2026-11-22) |
| **Ticket Key** | `AIML-0011-W1-01` |
| **Teammate (Events API)** | Prudhvi Kosuri (`AIML-0010-W1-01`) |
| **Recommendations Lead** | Adireddy Devendra (`AIML-0011-W1-01`) |

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
│   └── .gitkeep               # Preserves data directory structure for CSV/JSON files
├── src/
│   ├── __init__.py            # Module initializer and service version
│   └── main.py                # Service entry point & environment verification
├── tests/
│   └── test_setup.py          # Setup & dependency validation test suite
├── .gitignore                 # Excludes venv, pycache, temporary artifacts
├── Dockerfile                 # Multi-layer container specification
├── README.md                  # Service documentation & operations manual
└── requirements.txt           # Production & test dependencies
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

## 6. Application Execution

To run the Recommendations Service starter application:

```bash
# Ensure venv is activated
python src/main.py
```

### Expected Output
```text
============================================================
  BookMyShow Recommendations Service
  Team: AIML-04 | Ticket: AIML-0011-W1-01 | Sprint: 1
============================================================
Environment & Dependency Verification:
  - Python:       3.12.3
  - pandas:       2.3.3
  - numpy:        1.26.4
  - scikit-learn: 1.6.1
============================================================
Status: Service environment initialized successfully.
```

---

## 7. Testing Instructions

Automated tests are managed with `pytest`.

### Run All Setup Tests
From the `recommendations/` directory:
```bash
pytest
```

### Verbose Mode with Output Details
```bash
pytest -v -s tests/test_setup.py
```

### Expected Test Output
```text
tests/test_setup.py::test_pandas_import PASSED
tests/test_setup.py::test_numpy_import PASSED
tests/test_setup.py::test_sklearn_import PASSED
tests/test_setup.py::test_app_module_import PASSED
tests/test_setup.py::test_service_info PASSED
tests/test_setup.py::test_main_execution PASSED
========================== 6 passed in 0.45s ==========================
```

---

## 8. Docker Build and Run Instructions

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

## 9. Service Interface Contract (Team Coordination)

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

## 10. Git Workflow & Manual Instructions

All development for this ticket is isolated to the `recommendations/` directory on branch `AIML-0011-W1-01`.

### Step-by-Step Git Commands

1. **Verify Branch:**
   ```bash
   git branch --show-current
   # Output should be: AIML-0011-W1-01
   # If not: git checkout -b AIML-0011-W1-01
   ```

2. **Stage Only Recommendations Changes:**
   ```bash
   git add recommendations/
   ```

3. **Verify Staged Files:**
   ```bash
   git status
   ```
   Ensure `venv/` is **not** staged and only the intended files under `recommendations/` are listed.

4. **Commit Changes:**
   ```bash
   git commit -m "AIML-0011-W1-01: set up recommendations service environment and structure"
   ```

5. **Push Branch to GitHub:**
   ```bash
   git push origin AIML-0011-W1-01
   ```

6. **Create a Pull Request:**
   - Open GitHub: `https://github.com/Internectual-teams/aiml-04-2026-11-16-event-ticketing-platform`
   - Click **Compare & pull request** for `AIML-0011-W1-01`.
   - Set Base: `main` <- Compare: `AIML-0011-W1-01`.
   - Title: `AIML-0011-W1-01: Set up Python Environment and Git Repository (Recommendations Service)`
   - Assign teammate for review and link PR in the Internectual workspace.
