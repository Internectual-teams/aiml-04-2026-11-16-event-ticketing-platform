# Event Ticketing Platform

**Team AIML-04** · Internectual Project Team · Sprint 2026-11-16 to 2026-11-22

## Client: BookMyShow (fictional)

BookMyShow is a leading Indian online movie and events ticketing platform. They want to expand into smaller, local events and need a way to recommend relevant events to users based on their past behavior and event categories. The initial MVP should focus on core ticketing functionality and a simple recommendation system to validate the concept.

**Sprint goal:** Develop a basic event ticketing platform with a recommendation engine for the first sprint.

## Team and parts

- **Prudhvi Kosuri**: Events API Backend (integration owner this week)

- **Adireddy Devendra**: Recommendations Service

## Contract between the parts

## Project Structure

```
/
|-- events_api/
|   |-- app/
|   |   |-- __init__.py
|   |   |-- main.py
|   |   |-- models.py
|   |   |-- schemas.py
|   |-- tests/
|   |-- requirements.txt
|   |-- Dockerfile
|   |-- README.md
|
|-- recommendations/
|   |-- src/
|   |   |-- __init__.py
|   |   |-- data_processing.py
|   |   |-- recommendation_engine.py
|   |   |-- recommendation_output.py
|   |   |-- main.py
|   |-- tests/
|   |-- requirements.txt
|   |-- Dockerfile
|   |-- README.md
|
-- README.md
```

## Interfaces

**1. Events API (`events_api/`)**

*   **Purpose:** Manages event and ticket data.
*   **API Endpoints:**
    *   `POST /events`: Create a new event.
        *   Request Body: `{"name": "string", "description": "string", "category": "string", "date": "YYYY-MM-DDTHH:MM:SS", "price": float}`
        *   Response Body: `{"id": "uuid", "name": "string", ...}`
    *   `GET /events`: Get a list of all events.
        *   Response Body: `[{"id": "uuid", "name": "string", ...}]`
    *   `GET /events/{event_id}`: Get details of a specific event.
        *   Response Body: `{"id": "uuid", "name": "string", ...}`
    *   `POST /tickets`: Create a new ticket booking.
        *   Request Body: `{"event_id": "uuid", "user_id": "string", "quantity": int}`
        *   Response Body: `{"id": "uuid", "event_id": "uuid", "user_id": "string", ...}`
    *   `GET /tickets`: Get all ticket bookings.
        *   Response Body: `[{"id": "uuid", "event_id": "uuid", ...}]`

**2. Recommendations Service (`recommendations/`)**

*   **Purpose:** Generates event recommendations for users.
*   **Input:** A CSV file `user_event_history.csv` in the `data/` subdirectory with columns: `user_id`, `event_id`, `timestamp`.
*   **Output:** A JSON file `recommendations.json` in the `data/` subdirectory with user IDs and recommended event IDs: `{"user_id": ["event_id1", "event_id2", ...]}`.
*   **Function Signature (main processing function):**
    `def generate_recommendations(history_file_path: str, output_file_path: str) -> None`

## Running the Product

1.  **Set up virtual environments:**
    ```bash
    python -m venv events_api/venv
    source events_api/venv/bin/activate
    pip install -r events_api/requirements.txt
    deactivate

    python -m venv recommendations/venv
    source recommendations/venv/bin/activate
    pip install -r recommendations/requirements.txt
    deactivate
    ```
2.  **Run the Events API:**
    ```bash
    cd events_api
    source ../venv/bin/activate # If using a shared venv, otherwise use events_api/venv
    uvicorn app.main:app --reload --port 8000
    ```
3.  **Run the Recommendations Service:**
    *   Ensure `user_event_history.csv` is populated in the `recommendations/data/` directory.
    *   ```bash
        cd recommendations
        source ../venv/bin/activate # If using a shared venv, otherwise use recommendations/venv
        python src/main.py
        ```
4.  **Integration:** The Recommendations Service will read data that would typically be sourced from the Events API (simulated via CSV for this sprint). The README in the root directory will contain instructions and links to deployed services.

## How we work

1. Create a branch named after your ticket key (for example `aiml-07-w5-02`). Never push directly to `main`.

2. Build your ticket in your part's folder. Commit often with clear messages.

3. Open a pull request into `main` and submit the PR link on your ticket in the Internectual workspace.

4. Review one teammate's pull request every week (comment and approve).

5. The integration owner merges approved pull requests, makes everything run together, updates this README with run steps and the live demo link.



_This repository is private during the sprint and becomes public afterwards so you can show it in your portfolio._