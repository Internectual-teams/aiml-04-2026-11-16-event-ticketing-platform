"""FastAPI application for event listings and ticket bookings."""

from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException

# In the repository, use app.models. In the flat editor, use models instead.
from app.models import Event, EventCreate, Ticket, TicketCreate

app = FastAPI(title="Events API", version="0.1.0")

events: dict[UUID, Event] = {}
tickets: dict[UUID, Ticket] = {}


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


@app.post("/tickets", status_code=201, response_model=Ticket)
def create_ticket(ticket_data: TicketCreate) -> Ticket:
    ticket = Ticket(id=uuid4(), **ticket_data.model_dump())
    tickets[ticket.id] = ticket
    return ticket


@app.get("/tickets", response_model=list[Ticket])
def list_tickets() -> list[Ticket]:
    return list(tickets.values())