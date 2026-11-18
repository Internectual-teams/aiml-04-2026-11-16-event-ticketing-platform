"""Pydantic models for event request and response data."""

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
    """An event returned by the API, including its ID."""

    id: UUID