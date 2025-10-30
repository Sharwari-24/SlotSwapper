from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta

import crud, models, schemas
from database import engine, get_db, Base
from auth import create_access_token, verify_password, verify_access_token
from database import Base, engine
import models
from fastapi.responses import JSONResponse


Base.metadata.create_all(bind=engine)


# =====================================================
# ⚙️ Setup
# =====================================================
Base.metadata.create_all(bind=engine)
app = FastAPI(title="SlotSwapper API", version="1.0")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://127.0.0.1:5500"] if using Live Server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import traceback

@app.exception_handler(Exception)
async def debug_exceptions(request, exc):
    print("⚠️ INTERNAL SERVER ERROR:", exc)
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# =====================================================
# 🔐 Utility - Get Current User
# =====================================================
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    email = payload.get("sub")
    user = crud.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# =====================================================
# 🏠 Home
# =====================================================
@app.get("/")
def home():
    return {"message": "✅ SlotSwapper Backend is running!"}


# =====================================================
# 🧑 Signup
# =====================================================
@app.post("/signup", response_model=schemas.ShowUser)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = crud.create_user(db, user)
    return new_user


# =====================================================
# 🔑 Login
# =====================================================
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


# =====================================================
# 🗓️ Events
# =====================================================
@app.post("/events", response_model=schemas.EventShow)
def create_event(event: schemas.EventCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return crud.create_event(db, event, user_id=current_user.id)


@app.get("/events", response_model=list[schemas.EventShow])
def get_my_events(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return crud.get_user_events(db, current_user.id)


@app.patch("/events/{event_id}", response_model=schemas.EventShow)
def update_event_status(event_id: int, status: schemas.EventStatus, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    updated = crud.update_event_status(db, event_id, status, user_id=current_user.id)
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found or not owned by user")
    return updated


@app.get("/events/swappable", response_model=list[schemas.EventShow])
def get_swappable_events(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return crud.get_swappable_events(db, current_user.id)


# =====================================================
# 🔁 Swap Requests
# =====================================================
@app.post("/swap/request", response_model=schemas.SwapShow)
def request_swap(data: schemas.SwapRequestCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    swap = crud.create_swap_request(db, requester_id=current_user.id, data=data)
    if not swap:
        raise HTTPException(status_code=400, detail="Invalid swap request or slot not swappable")
    return swap


@app.get("/swap/incoming", response_model=list[schemas.SwapShow])
def incoming_requests(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return crud.get_incoming_requests(db, current_user.id)


@app.get("/swap/outgoing", response_model=list[schemas.SwapShow])
def outgoing_requests(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return crud.get_outgoing_requests(db, current_user.id)


@app.post("/swap/respond/{swap_id}", response_model=schemas.SwapShow)
def respond_to_swap(
    swap_id: int,
    response: schemas.SwapResponse,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    swap = crud.respond_to_swap(db, swap_id, accept=response.accept)
    if not swap:
        raise HTTPException(status_code=404, detail="Swap request not found")
    return swap



# 🧩 Test route

@app.get("/me")
def get_profile(current_user=Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email, "name": current_user.name}
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
import crud, schemas, models
from database import get_db
from auth import verify_access_token

# Helper: get current user
def get_current_user(token: str = Depends(verify_access_token), db: Session = Depends(get_db)):
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(models.User).filter(models.User.id == payload.get("id")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ✅ SWAPPABLE SLOTS ENDPOINT
@app.get("/swappable-slots")
def get_swappable_slots(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    events = crud.get_swappable_events(db, current_user.id)
    return events
