# Events API

FastAPI backend for the Event Ticketing Platform. It manages events and ticket bookings.

## Run locally

```bash
cd events_api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Then open http://127.0.0.1:8000/docs for the interactive API docs.

## Run with Docker

```bash
docker build -t events-api .
docker run -p 8000:8000 events-api
```