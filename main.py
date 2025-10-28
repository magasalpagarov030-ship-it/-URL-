from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Link
import string, random
from fastapi.responses import RedirectResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(title="URL Shortener API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class LinkCreate(BaseModel):
    url: HttpUrl

class LinkResponse(BaseModel):
    original_url: str
    short_url: str

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

@app.post("/shorten", response_model=LinkResponse)
def create_short_link(link: LinkCreate, db: Session = Depends(get_db)):
    existing = db.query(Link).filter(Link.original_url == link.url).first()
    if existing:
        return {"original_url": existing.original_url, "short_url": f"http://localhost:8000/{existing.short_code}"}

    short_code = generate_short_code()
    while db.query(Link).filter(Link.short_code == short_code).first():
        short_code = generate_short_code()

    new_link = Link(original_url=link.url, short_code=short_code)
    db.add(new_link)
    db.commit()
    db.refresh(new_link)

    return {"original_url": link.url, "short_url": f"http://localhost:8000/{short_code}"}

@app.get("/{short_code}")
def redirect_link(short_code: str, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")
    # реальный редирект в браузер
    return RedirectResponse(url=link.original_url)

@app.get("/links")
def list_links(db: Session = Depends(get_db)):
    return db.query(Link).all()
