"""Hifz Al-Na'ma backend: auth, role dashboards, food listings, reservations and admin API."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
import os, sqlite3, hashlib, hmac, secrets, json, base64
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr

DB_PATH = os.getenv('HIFZ_DB_PATH', str(Path(__file__).with_name('hifz_alnama.db')))
TOKEN_SECRET = os.getenv('HIFZ_TOKEN_SECRET', 'CHANGE_THIS_SECRET_BEFORE_DEPLOYMENT_' + secrets.token_hex(16))
TOKEN_TTL_HOURS = int(os.getenv('HIFZ_TOKEN_TTL_HOURS', '72'))
app = FastAPI(title="Hifz Al-Na'ma API", version="2.0.0", description="Accounts, role-based access, surplus food, reservations and admin dashboard")
origins = os.getenv('CORS_ORIGINS', '*').split(',')
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=['*'], allow_headers=['*'])

ROLES = {'restaurant', 'charity', 'individual', 'admin'}
ROLE_AR = {'restaurant':'مطعم / متجر', 'charity':'جمعية خيرية', 'individual':'فرد', 'admin':'مشرف'}
CATEGORIES = {'وجبات جاهزة','مخبوزات','خضروات وفواكه','حلويات'}

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str
    phone: str = Field(default='', max_length=30)
    city: str = Field(default='الباحة', max_length=80)
class LoginIn(BaseModel):
    email: EmailStr
    password: str
class FoodIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    category: str
    quantity: int = Field(gt=0, le=10000)
    expiry_at: datetime
    location_text: str = Field(min_length=2, max_length=250)
    description: str = Field(default='', max_length=500)
class ReservationIn(BaseModel):
    quantity: int = Field(gt=0, le=10000)
    note: str = Field(default='', max_length=300)
class UserStatusIn(BaseModel):
    active: bool
class FoodStatusIn(BaseModel):
    status: str
class ReservationStatusIn(BaseModel):
    status: str

def now_iso(): return datetime.now(timezone.utc).isoformat()
def connect():
    con=sqlite3.connect(DB_PATH, timeout=20)
    con.row_factory=sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    con.execute('PRAGMA journal_mode=WAL')
    return con

def hash_password(password, salt=None):
    salt=salt or secrets.token_bytes(16)
    digest=hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 310000)
    return base64.b64encode(salt).decode()+'.'+base64.b64encode(digest).decode()
def verify_password(password, stored):
    try:
        s,d=stored.split('.',1); salt=base64.b64decode(s); expected=base64.b64decode(d)
        return hmac.compare_digest(hashlib.pbkdf2_hmac('sha256',password.encode(),salt,310000),expected)
    except Exception: return False

def b64(data): return base64.urlsafe_b64encode(data).rstrip(b'=').decode()
def make_token(user):
    payload={'sub':user['id'],'role':user['role'],'exp':int((datetime.now(timezone.utc)+timedelta(hours=TOKEN_TTL_HOURS)).timestamp()),'nonce':secrets.token_hex(8)}
    raw=b64(json.dumps(payload,separators=(',',':')).encode())
    sig=b64(hmac.new(TOKEN_SECRET.encode(),raw.encode(),hashlib.sha256).digest())
    return raw+'.'+sig
def decode_token(token):
    try:
        raw,sig=token.split('.',1); expected=b64(hmac.new(TOKEN_SECRET.encode(),raw.encode(),hashlib.sha256).digest())
        if not hmac.compare_digest(sig,expected): raise ValueError()
        payload=json.loads(base64.urlsafe_b64decode(raw+'='*((4-len(raw)%4)%4)))
        if payload['exp'] < int(datetime.now(timezone.utc).timestamp()): raise ValueError()
        return payload
    except Exception: raise HTTPException(401,'انتهت الجلسة أو رمز الدخول غير صالح. سجّل الدخول مجددًا.')

def init_db():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT NOT NULL UNIQUE,password_hash TEXT NOT NULL,role TEXT NOT NULL,phone TEXT NOT NULL DEFAULT '',city TEXT NOT NULL DEFAULT '',active INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS foods(id INTEGER PRIMARY KEY AUTOINCREMENT,owner_id INTEGER NOT NULL REFERENCES users(id),name TEXT NOT NULL,category TEXT NOT NULL,quantity INTEGER NOT NULL CHECK(quantity>=0),expiry_at TEXT NOT NULL,location_text TEXT NOT NULL,description TEXT NOT NULL DEFAULT '',status TEXT NOT NULL DEFAULT 'available',created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS reservations(id INTEGER PRIMARY KEY AUTOINCREMENT,food_id INTEGER NOT NULL REFERENCES foods(id),requester_id INTEGER NOT NULL REFERENCES users(id),quantity INTEGER NOT NULL,note TEXT NOT NULL DEFAULT '',status TEXT NOT NULL DEFAULT 'reserved',created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_food_status_expiry ON foods(status,expiry_at);
        CREATE INDEX IF NOT EXISTS idx_reservation_requester ON reservations(requester_id,status);
        ''')
        # Seed an admin only when explicitly configured and no matching account exists.
        admin_email=os.getenv('HIFZ_ADMIN_EMAIL','').strip().lower(); admin_password=os.getenv('HIFZ_ADMIN_PASSWORD','')
        if admin_email and len(admin_password)>=12 and not db.execute('SELECT 1 FROM users WHERE email=?',(admin_email,)).fetchone():
            db.execute('INSERT INTO users(name,email,password_hash,role,phone,city,active,created_at) VALUES(?,?,?,?,?,?,1,?)',('مدير النظام',admin_email,hash_password(admin_password),'admin','', 'الباحة',now_iso()))
init_db()

def public_user(row):
    return {'id':row['id'],'name':row['name'],'email':row['email'],'role':row['role'],'role_ar':ROLE_AR.get(row['role'],row['role']),'phone':row['phone'],'city':row['city'],'active':bool(row['active']),'created_at':row['created_at']}
def current_user(authorization: Optional[str]=Header(default=None)):
    if not authorization or not authorization.lower().startswith('bearer '): raise HTTPException(401,'سجّل الدخول أولًا.')
    payload=decode_token(authorization.split(' ',1)[1])
    with connect() as db: user=db.execute('SELECT * FROM users WHERE id=?',(payload['sub'],)).fetchone()
    if not user or not user['active']: raise HTTPException(401,'الحساب غير موجود أو موقوف.')
    return dict(user)
def require_roles(*roles):
    def dep(user=Depends(current_user)):
        if user['role'] not in roles: raise HTTPException(403,'ليس لديك صلاحية لتنفيذ هذا الإجراء.')
        return user
    return dep

def food_json(r):
    return {'id':r['id'],'owner_id':r['owner_id'],'name':r['name'],'category':r['category'],'quantity':r['quantity'],'expiry_at':r['expiry_at'],'location_text':r['location_text'],'description':r['description'],'status':r['status'],'created_at':r['created_at'],'donor_name':r['owner_name'] if 'owner_name' in r.keys() else ''}
def reservation_json(r):
    return {'id':r['id'],'food_id':r['food_id'],'food_name':r['food_name'] if 'food_name' in r.keys() else '', 'requester_id':r['requester_id'],'requester_name':r['requester_name'] if 'requester_name' in r.keys() else '', 'quantity':r['quantity'],'note':r['note'],'status':r['status'],'created_at':r['created_at'],'updated_at':r['updated_at']}

@app.get('/')
def root(): return {'service':"Hifz Al-Na'ma API",'version':'2.0.0','docs':'/docs','health':'/api/health'}
@app.get('/api/health')
def health():
    with connect() as db: db.execute('SELECT 1')
    return {'status':'ok','database':'connected','version':'2.0.0'}
@app.post('/api/auth/register',status_code=201)
def register(payload:RegisterIn):
    role=payload.role.strip()
    if role not in {'restaurant','charity','individual'}: raise HTTPException(400,'نوع الحساب غير صالح.')
    email=payload.email.lower().strip()
    with connect() as db:
        if db.execute('SELECT 1 FROM users WHERE email=?',(email,)).fetchone(): raise HTTPException(409,'هذا البريد مسجل مسبقًا.')
        cur=db.execute('INSERT INTO users(name,email,password_hash,role,phone,city,active,created_at) VALUES(?,?,?,?,?,?,1,?)',(payload.name.strip(),email,hash_password(payload.password),role,payload.phone.strip(),payload.city.strip(),now_iso()))
        user=db.execute('SELECT * FROM users WHERE id=?',(cur.lastrowid,)).fetchone()
    return {'token':make_token(user),'user':public_user(user)}
@app.post('/api/auth/login')
def login(payload:LoginIn):
    with connect() as db: user=db.execute('SELECT * FROM users WHERE email=?',(payload.email.lower().strip(),)).fetchone()
    if not user or not verify_password(payload.password,user['password_hash']): raise HTTPException(401,'البريد الإلكتروني أو كلمة المرور غير صحيحة.')
    if not user['active']: raise HTTPException(403,'تم إيقاف الحساب. تواصل مع المشرف.')
    return {'token':make_token(user),'user':public_user(user)}
@app.get('/api/auth/me')
def me(user=Depends(current_user)): return {'user':public_user(user)}
@app.post('/api/auth/logout')
def logout(user=Depends(current_user)): return {'message':'تم تسجيل الخروج. احذف الرمز من جهازك. (الرمز صالح حتى انتهاء مدته إذا سُرق)'}

@app.get('/api/foods')
def list_foods(category:Optional[str]=None,include_unavailable:bool=False):
    sql='SELECT f.*,u.name AS owner_name FROM foods f JOIN users u ON u.id=f.owner_id WHERE 1=1'; args=[]
    if category and category in CATEGORIES: sql+=' AND f.category=?'; args.append(category)
    if not include_unavailable: sql+=" AND f.status='available' AND f.quantity>0 AND f.expiry_at>? AND u.active=1"; args.append(now_iso())
    sql+=' ORDER BY f.expiry_at ASC'
    with connect() as db: rows=db.execute(sql,args).fetchall()
    return [food_json(r) for r in rows]
@app.post('/api/foods',status_code=201)
def create_food(payload:FoodIn,user=Depends(require_roles('restaurant','charity','admin'))):
    if payload.category not in CATEGORIES: raise HTTPException(400,'التصنيف غير صالح.')
    exp=payload.expiry_at
    if exp.tzinfo is None: exp=exp.astimezone()
    if exp<=datetime.now().astimezone(): raise HTTPException(400,'وقت انتهاء الطعام يجب أن يكون في المستقبل.')
    with connect() as db:
        cur=db.execute("INSERT INTO foods(owner_id,name,category,quantity,expiry_at,location_text,description,status,created_at) VALUES(?,?,?,?,?,?,?,'available',?)",(user['id'],payload.name.strip(),payload.category,payload.quantity,exp.isoformat(),payload.location_text.strip(),payload.description.strip(),now_iso()))
        row=db.execute('SELECT f.*,u.name AS owner_name FROM foods f JOIN users u ON u.id=f.owner_id WHERE f.id=?',(cur.lastrowid,)).fetchone()
    return food_json(row)
@app.patch('/api/foods/{food_id}')
def update_food(food_id:int,payload:FoodIn,user=Depends(current_user)):
    with connect() as db:
        row=db.execute('SELECT * FROM foods WHERE id=?',(food_id,)).fetchone()
        if not row: raise HTTPException(404,'الوجبة غير موجودة.')
        if user['role']!='admin' and row['owner_id']!=user['id']: raise HTTPException(403,'يمكن للجهة المالكة فقط تعديل هذه الوجبة.')
        exp=payload.expiry_at if payload.expiry_at.tzinfo else payload.expiry_at.astimezone()
        if payload.category not in CATEGORIES or exp<=datetime.now().astimezone(): raise HTTPException(400,'تحقق من التصنيف ووقت الانتهاء.')
        db.execute('UPDATE foods SET name=?,category=?,quantity=?,expiry_at=?,location_text=?,description=? WHERE id=?',(payload.name,payload.category,payload.quantity,exp.isoformat(),payload.location_text,payload.description,food_id))
        updated=db.execute('SELECT f.*,u.name AS owner_name FROM foods f JOIN users u ON u.id=f.owner_id WHERE f.id=?',(food_id,)).fetchone()
    return food_json(updated)
@app.delete('/api/foods/{food_id}')
def delete_food(food_id:int,user=Depends(current_user)):
    with connect() as db:
        row=db.execute('SELECT * FROM foods WHERE id=?',(food_id,)).fetchone()
        if not row: raise HTTPException(404,'الوجبة غير موجودة.')
        if user['role']!='admin' and row['owner_id']!=user['id']: raise HTTPException(403,'ليس لديك صلاحية حذف هذه الوجبة.')
        db.execute("UPDATE foods SET status='cancelled' WHERE id=?",(food_id,))
    return {'message':'تم إلغاء نشر الوجبة.'}
@app.post('/api/foods/{food_id}/reservations',status_code=201)
def reserve_food(food_id:int,payload:ReservationIn,user=Depends(require_roles('charity','individual','admin'))):
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        food=db.execute('SELECT * FROM foods WHERE id=?',(food_id,)).fetchone()
        if not food: raise HTTPException(404,'الطعام غير موجود.')
        if food['owner_id']==user['id']: raise HTTPException(400,'لا يمكنك حجز فائض الجهة نفسها.')
        if food['status']!='available' or food['quantity']<=0 or food['expiry_at']<=now_iso(): raise HTTPException(409,'الطعام غير متاح للحجز.')
        if payload.quantity>food['quantity']: raise HTTPException(400,'الكمية المطلوبة أكبر من المتاح.')
        remaining=food['quantity']-payload.quantity
        db.execute('UPDATE foods SET quantity=?,status=? WHERE id=?',(remaining,'reserved' if remaining==0 else 'available',food_id))
        cur=db.execute("INSERT INTO reservations(food_id,requester_id,quantity,note,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",(food_id,user['id'],payload.quantity,payload.note.strip(),'reserved',now_iso(),now_iso()))
        r=db.execute('SELECT r.*,f.name AS food_name,u.name AS requester_name FROM reservations r JOIN foods f ON f.id=r.food_id JOIN users u ON u.id=r.requester_id WHERE r.id=?',(cur.lastrowid,)).fetchone()
    return reservation_json(r)
@app.get('/api/reservations')
def list_reservations(user=Depends(current_user)):
    with connect() as db:
        if user['role']=='admin': rows=db.execute('SELECT r.*,f.name AS food_name,u.name AS requester_name FROM reservations r JOIN foods f ON f.id=r.food_id JOIN users u ON u.id=r.requester_id ORDER BY r.id DESC').fetchall()
        elif user['role'] in {'restaurant'}: rows=db.execute('SELECT r.*,f.name AS food_name,u.name AS requester_name FROM reservations r JOIN foods f ON f.id=r.food_id JOIN users u ON u.id=r.requester_id JOIN foods own ON own.id=r.food_id WHERE own.owner_id=? ORDER BY r.id DESC',(user['id'],)).fetchall()
        else: rows=db.execute('SELECT r.*,f.name AS food_name,u.name AS requester_name FROM reservations r JOIN foods f ON f.id=r.food_id JOIN users u ON u.id=r.requester_id WHERE r.requester_id=? ORDER BY r.id DESC',(user['id'],)).fetchall()
    return [reservation_json(r) for r in rows]
@app.patch('/api/reservations/{reservation_id}')
def change_reservation(reservation_id:int,payload:ReservationStatusIn,user=Depends(current_user)):
    if payload.status not in {'reserved','completed','cancelled'}: raise HTTPException(400,'حالة الحجز غير صالحة.')
    with connect() as db:
        r=db.execute('SELECT r.*,f.owner_id,f.name AS food_name,u.name AS requester_name FROM reservations r JOIN foods f ON f.id=r.food_id JOIN users u ON u.id=r.requester_id WHERE r.id=?',(reservation_id,)).fetchone()
        if not r: raise HTTPException(404,'الحجز غير موجود.')
        if user['role']!='admin' and user['id'] not in (r['requester_id'],r['owner_id']): raise HTTPException(403,'ليس لديك صلاحية لتعديل هذا الحجز.')
        if r['status']=='cancelled' and payload.status!='cancelled': raise HTTPException(409,'لا يمكن إعادة تفعيل حجز ملغي تلقائيًا.')
        if payload.status=='cancelled' and r['status']=='reserved':
            db.execute('UPDATE foods SET quantity=quantity+?,status=CASE WHEN status=\'reserved\' THEN \'available\' ELSE status END WHERE id=?',(r['quantity'],r['food_id']))
        db.execute('UPDATE reservations SET status=?,updated_at=? WHERE id=?',(payload.status,now_iso(),reservation_id))
        updated=db.execute('SELECT r.*,f.name AS food_name,u.name AS requester_name FROM reservations r JOIN foods f ON f.id=r.food_id JOIN users u ON u.id=r.requester_id WHERE r.id=?',(reservation_id,)).fetchone()
    return reservation_json(updated)

@app.get('/api/dashboard')
def dashboard(user=Depends(current_user)):
    with connect() as db:
        if user['role']=='admin':
            stats={'users':db.execute('SELECT COUNT(*) FROM users').fetchone()[0],'foods':db.execute("SELECT COUNT(*) FROM foods WHERE status='available' AND quantity>0").fetchone()[0],'reservations':db.execute("SELECT COUNT(*) FROM reservations WHERE status='reserved'").fetchone()[0],'completed':db.execute("SELECT COUNT(*) FROM reservations WHERE status='completed'").fetchone()[0]}
            foods=db.execute('SELECT f.*,u.name AS owner_name FROM foods f JOIN users u ON u.id=f.owner_id ORDER BY f.id DESC LIMIT 50').fetchall()
            reservations=db.execute('SELECT r.*,f.name AS food_name,u.name AS requester_name FROM reservations r JOIN foods f ON f.id=r.food_id JOIN users u ON u.id=r.requester_id ORDER BY r.id DESC LIMIT 50').fetchall()
            users=db.execute('SELECT * FROM users ORDER BY id DESC LIMIT 100').fetchall()
            return {'role':user['role'],'stats':stats,'foods':[food_json(x) for x in foods],'reservations':[reservation_json(x) for x in reservations],'users':[public_user(x) for x in users]}
        if user['role']=='restaurant':
            foods=db.execute('SELECT f.*,u.name AS owner_name FROM foods f JOIN users u ON u.id=f.owner_id WHERE f.owner_id=? ORDER BY f.id DESC',(user['id'],)).fetchall()
            reservations=db.execute('SELECT r.*,f.name AS food_name,u.name AS requester_name FROM reservations r JOIN foods f ON f.id=r.food_id JOIN users u ON u.id=r.requester_id WHERE f.owner_id=? ORDER BY r.id DESC',(user['id'],)).fetchall()
            stats={'foods':len(foods),'available':sum(1 for x in foods if x['status']=='available' and x['quantity']>0),'reservations':len(reservations),'completed':sum(1 for x in reservations if x['status']=='completed')}
        else:
            reservations=db.execute('SELECT r.*,f.name AS food_name,u.name AS requester_name FROM reservations r JOIN foods f ON f.id=r.food_id JOIN users u ON u.id=r.requester_id WHERE r.requester_id=? ORDER BY r.id DESC',(user['id'],)).fetchall()
            foods=[]; stats={'reservations':len(reservations),'active':sum(1 for x in reservations if x['status']=='reserved'),'completed':sum(1 for x in reservations if x['status']=='completed')}
        return {'role':user['role'],'stats':stats,'foods':[food_json(x) for x in foods],'reservations':[reservation_json(x) for x in reservations]}

@app.get('/api/admin/users')
def admin_users(user=Depends(require_roles('admin'))):
    with connect() as db: rows=db.execute('SELECT * FROM users ORDER BY id DESC').fetchall()
    return [public_user(r) for r in rows]
@app.patch('/api/admin/users/{user_id}')
def admin_set_user(user_id:int,payload:UserStatusIn,user=Depends(require_roles('admin'))):
    if user_id==user['id'] and not payload.active: raise HTTPException(400,'لا يمكنك إيقاف حسابك الحالي.')
    with connect() as db:
        cur=db.execute('UPDATE users SET active=? WHERE id=?',(1 if payload.active else 0,user_id))
        if cur.rowcount==0: raise HTTPException(404,'المستخدم غير موجود.')
        row=db.execute('SELECT * FROM users WHERE id=?',(user_id,)).fetchone()
    return public_user(row)
@app.patch('/api/admin/foods/{food_id}')
def admin_set_food(food_id:int,payload:FoodStatusIn,user=Depends(require_roles('admin'))):
    if payload.status not in {'available','reserved','completed','cancelled'}: raise HTTPException(400,'حالة الوجبة غير صالحة.')
    with connect() as db:
        cur=db.execute('UPDATE foods SET status=? WHERE id=?',(payload.status,food_id))
        if not cur.rowcount: raise HTTPException(404,'الوجبة غير موجودة.')
        row=db.execute('SELECT f.*,u.name AS owner_name FROM foods f JOIN users u ON u.id=f.owner_id WHERE f.id=?',(food_id,)).fetchone()
    return food_json(row)
