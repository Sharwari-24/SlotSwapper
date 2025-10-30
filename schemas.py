from pydantic import BaseModel
from datetime import datetime
from enum import Enum


# ======================================
# 🧑 USER SCHEMAS
# ======================================

class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class ShowUser(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True  # For SQLAlchemy ORM conversion


# ======================================
# 🗓️ EVENT SCHEMAS
# ======================================

class EventStatus(str, Enum):
    BUSY = "BUSY"
    SWAPPABLE = "SWAPPABLE"
    SWAP_PENDING = "SWAP_PENDING"


class EventBase(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    status: EventStatus = EventStatus.BUSY


class EventCreate(EventBase):
    pass


class EventShow(EventBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


# ======================================
# 🔁 SWAP SCHEMAS
# ======================================

class SwapRequestCreate(BaseModel):
    my_slot_id: int
    their_slot_id: int


class SwapResponse(BaseModel):
    accept: bool


class SwapShow(BaseModel):
    id: int
    requester_id: int
    responder_id: int
    requester_event_id: int
    responder_event_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
