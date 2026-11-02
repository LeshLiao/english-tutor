from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ErrorTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    created_at: datetime


class SentenceErrorIn(BaseModel):
    error_type: str = Field(
        ..., min_length=1, max_length=100,
        description="錯誤類型名稱；不存在會自動新增。優先沿用 GET /error-types 的現有名稱。",
    )
    error_snippet: str = Field(..., description="原句中出錯的片段")
    suggestion: str = Field(..., description="建議改法")
    description: str | None = Field(None, description="僅在新增類型時用來當 error_types.description")


class SentenceCreate(BaseModel):
    original_text: str = Field(..., min_length=1)
    corrected_text: str
    explanation: str = ""
    source: Literal["hook", "skill"]
    errors: list[SentenceErrorIn] = []


class SentenceErrorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    error_type: ErrorTypeOut
    error_snippet: str
    suggestion: str


class SentenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_text: str
    corrected_text: str
    explanation: str
    source: str
    is_dismissed: bool
    created_at: datetime
    errors: list[SentenceErrorOut]


class ErrorStat(BaseModel):
    error_type_id: int
    error_type: str
    count: int


class HealthOut(BaseModel):
    status: str
    database: str
