from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import ErrorType
from app.schemas import ErrorTypeOut

router = APIRouter(prefix="/error-types", tags=["error-types"])


@router.get("", response_model=list[ErrorTypeOut])
def list_error_types(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """列出所有錯誤類型（全域共用，不分使用者）。"""
    return db.scalars(select(ErrorType).order_by(ErrorType.name)).all()
