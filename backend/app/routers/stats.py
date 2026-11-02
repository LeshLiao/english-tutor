from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import ErrorType, Sentence, SentenceError, User
from app.schemas import ErrorStat

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/errors", response_model=list[ErrorStat])
def error_stats(
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """各錯誤類型出現次數（排除已標記誤判的句子）。"""
    stmt = (
        select(ErrorType.id, ErrorType.name, func.count(SentenceError.id).label("count"))
        .join(SentenceError, SentenceError.error_type_id == ErrorType.id)
        .join(Sentence, Sentence.id == SentenceError.sentence_id)
        .where(Sentence.user_id == user.id, Sentence.is_dismissed.is_(False))
    )
    if from_:
        stmt = stmt.where(Sentence.created_at >= from_)
    if to:
        stmt = stmt.where(Sentence.created_at <= to)
    stmt = stmt.group_by(ErrorType.id, ErrorType.name).order_by(func.count(SentenceError.id).desc())
    return [
        ErrorStat(error_type_id=row.id, error_type=row.name, count=row.count)
        for row in db.execute(stmt)
    ]
