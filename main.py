"""Hifz Al-Na'ma API starter. Run: uvicorn main:app --reload"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Hifz Al-Na'ma API", version="0.1.0", description="API starter for surplus-food donation and reservation workflows")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5500", "http://127.0.0.1:5500", "http://localhost:8000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class Category(str, Enum):
    ready_meals = "وجبات جاهزة"
    bakery = "مخبوزات"
    produce = "خضروات وفواكه"
    sweets = "حلويات"

class FoodCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    category: Category
    quantity: int = Field(gt=0, le=10000)
    expiry_at: datetime
    donor_name: str = Field(min_length=2, max_length=120)
    location_text: str = Field(min_length=2, max_length=250)
    image_url: Optional[str] = None

class Food(FoodCreate):
    id: int
    status: str = "available"
    created_at: datetime

class ReservationCreate(BaseModel):
    organization_name: str = Field(min_length=2, max_length=120)
    quantity: int = Field(gt=0)

class Reservation(BaseModel):
    id: int
    food_id: int
    organization_name: str
    quantity: int
    status: str = "reserved"
    created_at: datetime

foods: dict[int, Food] = {}
reservations: dict[int, Reservation] = {}
food_counter = 1
reservation_counter = 1

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "hifz-alnama-api", "time": datetime.now(timezone.utc)}

@app.get("/api/foods", response_model=list[Food])
def list_foods(category: Optional[Category] = None):
    rows = list(foods.values())
    if category:
        rows = [f for f in rows if f.category == category]
    return sorted(rows, key=lambda f: f.expiry_at)

@app.post("/api/foods", response_model=Food, status_code=201)
def create_food(payload: FoodCreate):
    global food_counter
    if payload.expiry_at <= datetime.now(payload.expiry_at.tzinfo) if payload.expiry_at.tzinfo else payload.expiry_at <= datetime.now():
        raise HTTPException(status_code=400, detail="expiry_at must be in the future")
    food = Food(id=food_counter, **payload.model_dump(), created_at=datetime.now(timezone.utc))
    foods[food_counter] = food
    food_counter += 1
    return food

@app.post("/api/foods/{food_id}/reservations", response_model=Reservation, status_code=201)
def reserve_food(food_id: int, payload: ReservationCreate):
    global reservation_counter
    food = foods.get(food_id)
    if not food:
        raise HTTPException(status_code=404, detail="Food listing not found")
    if food.status != "available":
        raise HTTPException(status_code=409, detail="Food listing is not available")
    if payload.quantity > food.quantity:
        raise HTTPException(status_code=400, detail="Requested quantity exceeds available quantity")
    # Starter behavior: a single reservation closes the listing to avoid overbooking.
    reservation = Reservation(id=reservation_counter, food_id=food_id, organization_name=payload.organization_name, quantity=payload.quantity, created_at=datetime.now(timezone.utc))
    reservations[reservation_counter] = reservation
    reservation_counter += 1
    foods[food_id] = food.model_copy(update={"quantity": food.quantity - payload.quantity, "status": "reserved" if food.quantity == payload.quantity else "available"})
    return reservation

@app.get("/api/reservations", response_model=list[Reservation])
def list_reservations():
    return list(reservations.values())
