"""
Diary endpoints — read and manually trigger generation.
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.deps import get_current_user
from models import Diary
from services.supabase_client import get_db
from services.claude_service import get_claude

router = APIRouter(prefix="/diaries", tags=["diaries"])


# ---- Schemas ----

class DiaryOut(BaseModel):
    id: str
    diary_date: str
    content: str
    fragment_count: int
    created_at: str


class DiaryListResponse(BaseModel):
    diaries: list[DiaryOut]


# ---- Endpoints ----

@router.post("/generate")
async def generate_diary(
    target_date: date = Query(default=None, description="日期，默认今天"),
    openid: str = Depends(get_current_user),
):
    """手动触发日记生成."""
    db = get_db()
    claude = get_claude()

    target = target_date or date.today()

    fragments = await db.get_fragments_by_date(openid, target)
    if not fragments:
        raise HTTPException(status_code=400, detail="当天没有碎片，无法生成日记")

    diary_text = await claude.synthesize_diary(fragments, target)

    diary = Diary(
        user_id=openid,
        diary_date=target,
        content=diary_text,
        fragment_ids=[f.id for f in fragments if f.id],
    )
    saved = await db.save_diary(diary)

    return DiaryOut(
        id=str(saved.id),
        diary_date=saved.diary_date.isoformat(),
        content=saved.content,
        fragment_count=len(fragments),
        created_at=saved.created_at.isoformat() if saved.created_at else "",
    )


@router.get("/today")
async def get_today_diary(openid: str = Depends(get_current_user)):
    """获取今天的日记."""
    db = get_db()
    diary = await db.get_diary(openid, date.today())
    if not diary:
        raise HTTPException(status_code=404, detail="今天还没有生成日记")

    return DiaryOut(
        id=str(diary.id),
        diary_date=diary.diary_date.isoformat(),
        content=diary.content,
        fragment_count=len(diary.fragment_ids),
        created_at=diary.created_at.isoformat() if diary.created_at else "",
    )


@router.get("/history", response_model=DiaryListResponse)
async def get_diary_history(
    days: int = Query(default=30, ge=1, le=365),
    openid: str = Depends(get_current_user),
):
    """获取历史日记列表."""
    db = get_db()
    diaries = await db.get_recent_diaries(openid, days=days)

    return DiaryListResponse(
        diaries=[
            DiaryOut(
                id=str(d.id),
                diary_date=d.diary_date.isoformat(),
                content=d.content,
                fragment_count=len(d.fragment_ids),
                created_at=d.created_at.isoformat() if d.created_at else "",
            )
            for d in diaries
        ]
    )


@router.get("/{diary_date}")
async def get_diary_by_date(
    diary_date: date,
    openid: str = Depends(get_current_user),
):
    """获取指定日期的日记."""
    db = get_db()
    diary = await db.get_diary(openid, diary_date)
    if not diary:
        raise HTTPException(status_code=404, detail="该日期没有日记")

    return DiaryOut(
        id=str(diary.id),
        diary_date=diary.diary_date.isoformat(),
        content=diary.content,
        fragment_count=len(diary.fragment_ids),
        created_at=diary.created_at.isoformat() if diary.created_at else "",
    )
