"""Data models — Pydantic schemas for type safety."""

from __future__ import annotations

from datetime import datetime, date
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class FragmentType(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    PHOTO = "photo"


class Fragment(BaseModel):
    id: UUID | None = None
    user_id: str               # WeChat openid
    type: FragmentType
    content: str | None = None
    media_url: str | None = None
    metadata: dict = {}
    created_at: datetime | None = None


class Diary(BaseModel):
    id: UUID | None = None
    user_id: str               # WeChat openid
    diary_date: date
    content: str
    fragment_ids: list[UUID] = []
    created_at: datetime | None = None


class User(BaseModel):
    id: str                    # WeChat openid
    nickname: str | None = None
    avatar_url: str | None = None
    timezone: str = "Asia/Shanghai"
