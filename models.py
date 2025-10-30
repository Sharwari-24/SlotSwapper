# models.py
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import datetime

class EventStatus(str, enum.Enum):
    BUSY = "BUSY"
    SWAPPABLE = "SWAPPABLE"
    SWAP_PENDING = "SWAP_PENDING"

class SwapStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    events = relationship("Event", back_populates="owner")
    # optional: swap requests relationship if needed

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(Enum(EventStatus), default=EventStatus.BUSY)
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="events")

class SwapRequest(Base):
    __tablename__ = "swap_requests"
    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"))   # user who initiated the swap
    responder_id = Column(Integer, ForeignKey("users.id"))   # owner of the requested slot
    requester_event_id = Column(Integer, ForeignKey("events.id"))
    responder_event_id = Column(Integer, ForeignKey("events.id"))
    status = Column(Enum(SwapStatus), default=SwapStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
