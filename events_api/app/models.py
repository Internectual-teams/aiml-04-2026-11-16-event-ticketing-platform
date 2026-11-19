"""Pydantic models for event and ticket API data."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    """Fields required when creating an event."""

    name: str
    description: str
    category: str
    date: datetime
    price: float = Field(ge=0)


class Event(EventCreate):
    """An event returned by the API."""

    id: UUID


class TicketCreate(BaseModel):
    """Fields required when booking tickets."""

    event_id: UUID
    user_id: str
    quantity: int = Field(gt=0)


class Ticket(TicketCreate):
    """A ticket booking returned by the API."""

    id: UUID