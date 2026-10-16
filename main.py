"""Hifz Al-Na'ma API with SQLite persistence. Run: uvicorn main:app --host 0.0.0.0 --port 8000"""
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import os, sqlite3
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DB_PATH = os.getenv('HIFZ_DB_PATH', str(Path(__file__).with_name('hifz_alnama.db')))
app = FastAPI(title="Hifz Al-Na'ma API", version="1.0.0", description="Persistent API for surplus-food donations and reservations")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv('CORS_ORIGINS', '*').split(','), allow_credentials=False, allow_methods=['*'], allow_headers=['*'])

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

class Food(BaseModel):
    id: int
    name: str
    category: Category
    quantity: int
    expiry_at: datetime
    donor_name: str
    location_text: str
    image_url: Optional[str] = None
    status: str
    created_at: datetime

class ReservationCreate(BaseModel):
    organization_name: str = Field(min_length=2, max_length=120)
    quantity: int = Field(gt=0, le=10000)

class Reservation(BaseModel):
    id: int
    food_id: int
    organization_name: str
    quantity: int
    status: str
    created_at: datetime

def connect():
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    return con

def init_db():
    with connect() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS foods (
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, category TEXT NOT NULL,
          quantity INTEGER NOT NULL CHECK(quantity >= 0), expiry_at TEXT NOT NULL,
          donor_name TEXT NOT NULL, location_text TEXT NOT NULL, image_url TEXT,
          status TEXT NOT NULL DEFAULT 'available', created_at TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS reservations (
          id INTEGER PRIMARY KEY AUTOINCREMENT, food_id INTEGER NOT NULL REFERENCES foods(id),
          organization_name TEXT NOT NULL, quantity INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'reserved',
          created_at TEXT NOT NULL)''')
init_db()

def iso_now(): return datetime.now(timezone.utc).isoformat()
def food_row(r):
    return Food(id=r['id'], name=r['name'], category=r['category'], quantity=r['quantity'], expiry_at=r['expiry_at'], donor_name=r['donor_name'], location_text=r['location_text'], image_url=r['image_url'], status=r['status'], created_at=r['created_at'])
def reservation_row(r): return Reservation(**dict(r))

@app.get('/')
def root(): return {'service': "Hifz Al-Na'ma API", 'docs': '/docs', 'health': '/api/health'}
@app.get('/api/health')
def health(): return {'status':'ok','service':'hifz-alnama-api','database':'sqlite'}
@app.get('/api/foods', response_model=list[Food])
def list_foods(category: Optional[Category] = None, include_unavailable: bool = False):
    sql='SELECT * FROM foods WHERE 1=1'; args=[]
    if category: sql+=' AND category=?'; args.append(category.value)
    if not include_unavailable: sql+=" AND status='available' AND quantity>0 AND expiry_at>?"; args.append(iso_now())
    sql+=' ORDER BY expiry_at ASC'
    with connect() as db: rows=db.execute(sql,args).fetchall()
    return [food_row(r) for r in rows]
@app.post('/api/foods', response_model=Food, status_code=201)
def create_food(payload: FoodCreate):
    exp=payload.expiry_at
    if exp.tzinfo is None: exp=exp.astimezone()
    if exp <= datetime.now().astimezone(): raise HTTPException(400, 'وقت انتهاء الطعام يجب أن يكون في المستقبل')
    with connect() as db:
        cur=db.execute('INSERT INTO foods(name,category,quantity,expiry_at,donor_name,location_text,image_url,status,created_at) VALUES(?,?,?,?,?,?,?,\'available\',?)', (payload.name,payload.category.value,payload.quantity,exp.isoformat(),payload.donor_name,payload.location_text,payload.image_url,iso_now()))
        row=db.execute('SELECT * FROM foods WHERE id=?',(cur.lastrowid,)).fetchone()
    return food_row(row)
@app.post('/api/foods/{food_id}/reservations', response_model=Reservation, status_code=201)
def reserve_food(food_id: int, payload: ReservationCreate):
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        food=db.execute('SELECT * FROM foods WHERE id=?',(food_id,)).fetchone()
        if not food: raise HTTPException(404,'الطعام غير موجود')
        if food['status']!='available' or food['quantity']<=0: raise HTTPException(409,'الطعام غير متاح للحجز')
        if payload.quantity>food['quantity']: raise HTTPException(400,'الكمية المطلوبة أكبر من المتاح')
        now=iso_now(); remaining=food['quantity']-payload.quantity
        db.execute('UPDATE foods SET quantity=?, status=? WHERE id=?',(remaining,'reserved' if remaining==0 else 'available',food_id))
        cur=db.execute('INSERT INTO reservations(food_id,organization_name,quantity,status,created_at) VALUES(?,?,?,\'reserved\',?)',(food_id,payload.organization_name,payload.quantity,now))
        row=db.execute('SELECT * FROM reservations WHERE id=?',(cur.lastrowid,)).fetchone()
    return reservation_row(row)
@app.get('/api/reservations', response_model=list[Reservation])
def list_reservations():
    with connect() as db: rows=db.execute('SELECT * FROM reservations ORDER BY id DESC').fetchall()
    return [reservation_row(r) for r in rows]
