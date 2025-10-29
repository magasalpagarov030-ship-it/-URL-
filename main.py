from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Link, User
import string, random
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

# === Настройки ===
SECRET_KEY = "super_secret_key_123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="URL Shortener with Auth")

# ========== БАЗА ==========
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========== СХЕМЫ ==========
class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class LinkCreate(BaseModel):
    url: HttpUrl

class LinkResponse(BaseModel):
    original_url: str
    short_url: str

# ========== УТИЛИТЫ ==========
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user(db, username: str):
    return db.query(User).filter(User.username == username).first()

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=username)
    if user is None:
        raise credentials_exception
    return user

# ========== РЕГИСТРАЦИЯ / ЛОГИН ==========
@app.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if get_user(db, user.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_pw = get_password_hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    token = create_access_token({"sub": new_user.username})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# ========== СОКРАЩЕНИЕ ССЫЛОК ==========
def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

@app.post("/shorten", response_model=LinkResponse)
def create_short_link(link: LinkCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    short_code = generate_short_code()
    while db.query(Link).filter(Link.short_code == short_code).first():
        short_code = generate_short_code()

    new_link = Link(original_url=link.url, short_code=short_code, user_id=user.id)
    db.add(new_link)
    db.commit()
    db.refresh(new_link)

    return {"original_url": link.url, "short_url": f"http://localhost:8000/{short_code}"}

@app.get("/{short_code}")
def redirect_link(short_code: str, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")
    link.clicks += 1
    db.commit()
    return RedirectResponse(url=link.original_url)

@app.get("/links")
def list_links(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    links = db.query(Link).filter(Link.user_id == user.id).all()
    return [
        {
            "id": l.id,
            "original_url": l.original_url,
            "short_url": f"http://localhost:8000/{l.short_code}",
            "clicks": l.clicks
        } for l in links
    ]
