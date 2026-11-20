## Set up the project

Run these commands from the repository root:

```bash
python3 -m venv events_api/venv
source events_api/venv/bin/activate
pip install -r events_api/requirements.txt
deactivate

python3 -m venv recommendations/venv
source recommendations/venv/bin/activate
pip install -r recommendations/requirements.txt
deactivate
```

## Run the Events API

Open a terminal:

```bash
cd events_api
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Open http://127.0.0.1:8000/docs to try the API.

## Run Recommendations

Open a second terminal:

```bash
cd recommendations
source venv/bin/activate
python -m pytest tests
python src/main.py
```

The recommendations script reads `data/user_event_history.csv` and writes
`data/recommendations.json`. For this sprint, the history data is provided by
the CSV file.

## Live Events API

- API: ADD-THE-REAL-DEPLOYED-URL-HERE
- Interactive docs: ADD-THE-REAL-DEPLOYED-URL-HERE/docs