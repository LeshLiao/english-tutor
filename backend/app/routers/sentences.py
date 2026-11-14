from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import ErrorType, Sentence, SentenceError, User
from app.schemas import SentenceCreate, SentenceOut, SentenceUpdate

router = APIRouter(prefix="/sentences", tags=["sentences"])


def get_or_create_error_type(db: Session, name: str, description: str | None) -> ErrorType:
    normalized = name.strip().lower()
    et = db.scalar(select(ErrorType).where(ErrorType.name == normalized))
    if et is None:
        et = ErrorType(name=normalized, description=description)
        db.add(et)
        db.flush()
    return et


@router.post("", response_model=SentenceOut, status_code=status.HTTP_201_CREATED)
def create_sentence(
    payload: SentenceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """儲存一筆句子與其錯誤。錯誤類型用名稱指定，不存在會自動新增。"""
    sentence = Sentence(
        user_id=user.id,
        original_text=payload.original_text,
        corrected_text=payload.corrected_text,
        explanation=payload.explanation,
        source=payload.source,
    )
    for err in payload.errors:
        et = get_or_create_error_type(db, err.error_type, err.description)
        sentence.errors.append(
            SentenceError(error_type=et, error_snippet=err.error_snippet, suggestion=err.suggestion)
        )
    db.add(sentence)
    db.commit()
    db.refresh(sentence)
    return sentence


@router.get("", response_model=list[SentenceOut])
def list_sentences(
    error_type: str | None = Query(None, description="依錯誤類型名稱篩選"),
    q: str | None = Query(None, min_length=1, description="關鍵字，不分大小寫比對原句與修正句"),
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    include_dismissed: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Sentence).where(Sentence.user_id == user.id)
    if not include_dismissed:
        stmt = stmt.where(Sentence.is_dismissed.is_(False))
    if error_type:
        stmt = stmt.where(
            Sentence.errors.any(SentenceError.error_type.has(ErrorType.name == error_type.strip().lower()))
        )
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(or_(Sentence.original_text.ilike(pattern), Sentence.corrected_text.ilike(pattern)))
    if from_:
        stmt = stmt.where(Sentence.created_at >= from_)
    if to:
        stmt = stmt.where(Sentence.created_at <= to)
    stmt = stmt.order_by(Sentence.created_at.desc(), Sentence.id.desc()).limit(limit).offset(offset)
    return db.scalars(stmt).all()


def _get_own_sentence(db: Session, user: User, sentence_id: int) -> Sentence:
    sentence = db.get(Sentence, sentence_id)
    if sentence is None or sentence.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sentence not found")
    return sentence


@router.get("/{sentence_id}", response_model=SentenceOut)
def get_sentence(
    sentence_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _get_own_sentence(db, user, sentence_id)


@router.patch("/{sentence_id}", response_model=SentenceOut)
def update_sentence(
    sentence_id: int,
    payload: SentenceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """更新 is_dismissed（標記誤判或取消標記）。"""
    sentence = _get_own_sentence(db, user, sentence_id)
    sentence.is_dismissed = payload.is_dismissed
    db.commit()
    db.refresh(sentence)
    return sentence


@router.delete("/{sentence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sentence(
    sentence_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """永久刪除一筆句子及其錯誤紀錄（無法復原；只想排除統計請用 PATCH is_dismissed）。"""
    sentence = _get_own_sentence(db, user, sentence_id)
    db.delete(sentence)
    db.commit()
