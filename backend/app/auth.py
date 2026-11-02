from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_current_user(
    api_key: str | None = Depends(api_key_header),
    db: Session = Depends(get_db),
) -> User:
    if not api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing X-API-Key header")
    user = db.scalar(select(User).where(User.api_key == api_key))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")
    return user
