from sqlalchemy.orm import Session
from sqlalchemy import or_
import models, schemas
from auth import get_password_hash
from datetime import datetime


# ======================================
# 🧑 USER CRUD
# ======================================

def get_user_by_email(db: Session, email: str):
    """Fetch user by email."""
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate):
    """Create a new user with hashed password (with debug logging)."""
    try:
        print(f"🟡 Creating user: {user.email}")

        hashed_password = get_password_hash(user.password)
        print("✅ Password hashed successfully")

        db_user = models.User(
            name=user.name,
            email=user.email,
            password=hashed_password
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        print("✅ User created successfully")
        return db_user

    except Exception as e:
        print("❌ Error while creating user:", e)
        raise e



# ======================================
# 🗓️ EVENT CRUD
# ======================================

def create_event(db: Session, event: schemas.EventCreate, user_id: int):
    """Create a new event for a user."""
    db_event = models.Event(
        title=event.title,
        start_time=event.start_time,
        end_time=event.end_time,
        status=event.status,
        user_id=user_id
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def get_user_events(db: Session, user_id: int):
    """Return all events belonging to a specific user."""
    return db.query(models.Event).filter(models.Event.user_id == user_id).all()


def update_event_status(db: Session, event_id: int, new_status: schemas.EventStatus, user_id: int):
    """Update an event’s status (e.g., BUSY -> SWAPPABLE)."""
    db_event = db.query(models.Event).filter(
        models.Event.id == event_id, models.Event.user_id == user_id
    ).first()

    if db_event:
        db_event.status = new_status
        db.commit()
        db.refresh(db_event)
    return db_event


def get_swappable_events(db: Session, current_user_id: int):
    """Get all swappable slots excluding the current user’s own."""
    return db.query(models.Event).filter(
        models.Event.status == schemas.EventStatus.SWAPPABLE,
        models.Event.user_id != current_user_id
    ).all()


# ======================================
# 🔁 SWAP LOGIC
# ======================================

def create_swap_request(db: Session, requester_id: int, data: schemas.SwapRequestCreate):
    """Create a new swap request between two events."""
    my_event = db.query(models.Event).filter(
        models.Event.id == data.my_slot_id,
        models.Event.user_id == requester_id,
        models.Event.status == schemas.EventStatus.SWAPPABLE
    ).first()

    their_event = db.query(models.Event).filter(
        models.Event.id == data.their_slot_id,
        models.Event.status == schemas.EventStatus.SWAPPABLE
    ).first()

    if not my_event or not their_event:
        return None

    swap_request = models.SwapRequest(
        requester_id=requester_id,
        responder_id=their_event.user_id,
        requester_event_id=my_event.id,
        responder_event_id=their_event.id,
        status="PENDING"
    )

    # Set both events to SWAP_PENDING
    my_event.status = schemas.EventStatus.SWAP_PENDING
    their_event.status = schemas.EventStatus.SWAP_PENDING

    db.add(swap_request)
    db.commit()
    db.refresh(swap_request)
    return swap_request


def get_incoming_requests(db: Session, user_id: int):
    """List swap requests received by the user."""
    return db.query(models.SwapRequest).filter(models.SwapRequest.responder_id == user_id).all()


def get_outgoing_requests(db: Session, user_id: int):
    """List swap requests made by the user."""
    return db.query(models.SwapRequest).filter(models.SwapRequest.requester_id == user_id).all()


def respond_to_swap(db: Session, swap_id: int, accept: bool):
    """Handle swap acceptance/rejection."""
    swap = db.query(models.SwapRequest).filter(models.SwapRequest.id == swap_id).first()
    if not swap:
        return None

    requester_event = db.query(models.Event).filter(models.Event.id == swap.requester_event_id).first()
    responder_event = db.query(models.Event).filter(models.Event.id == swap.responder_event_id).first()

    if accept:
        # Swap ownership
        requester_id = swap.requester_id
        responder_id = swap.responder_id
        requester_event.user_id, responder_event.user_id = responder_id, requester_id
        requester_event.status = responder_event.status = schemas.EventStatus.BUSY
        swap.status = "ACCEPTED"
    else:
        # Reset both to SWAPPABLE
        requester_event.status = responder_event.status = schemas.EventStatus.SWAPPABLE
        swap.status = "REJECTED"

    swap.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(swap)
    return swap
