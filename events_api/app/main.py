"""FastAPI application for managing event listings."""

from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException

# The repository uses app.models. In a flat Internectual workspace, use
# `from models import Event, EventCreate` instead.
from app.models import Event, EventCreate

app = FastAPI(title="Events API", version="0.1.0")

events: dict[UUID, Event] = {}


@app.get("/")
def root():
    return {"message": "Events API is running"}


@app.post("/events", status_code=201, response_model=Event)
def create_event(event_data: EventCreate) -> Event:
    event = Event(id=uuid4(), **event_data.model_dump())
    events[event.id] = event
    return event


@app.get("/events", response_model=list[Event])
def list_events() -> list[Event]:
    return list(events.values())


@app.get("/events/{event_id}", response_model=Event)
def get_event(event_id: UUID) -> Event:
    event = events.get(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event