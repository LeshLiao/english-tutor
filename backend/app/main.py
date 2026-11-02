import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal, get_db
from app.models import User
from app.routers import error_types, sentences, stats
from app.schemas import HealthOut

log = logging.getLogger("uvicorn.error")


def seed_default_user() -> None:
    """確保有一個預設使用者，api_key 取自環境變數 API_KEY。資料表還沒建好時只警告不中斷。"""
    try:
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.name == settings.default_user_name))
            if user is None:
                db.add(User(name=settings.default_user_name, api_key=settings.api_key))
                log.info("seeded default user")
            elif user.api_key != settings.api_key:
                user.api_key = settings.api_key
                log.info("updated default user api_key")
            db.commit()
    except Exception as exc:  # noqa: BLE001
        log.warning("seed skipped (run `alembic upgrade head` first): %s", exc)


@asynccontextmanager
async def lifespan(_: FastAPI):
    seed_default_user()
    yield


app = FastAPI(title="English Tutor API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(error_types.router)
app.include_router(sentences.router)
app.include_router(stats.router)


@app.get("/health", response_model=HealthOut, tags=["health"])
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return HealthOut(status="ok", database="ok")
    except Exception:  # noqa: BLE001
        return HealthOut(status="degraded", database="unreachable")
