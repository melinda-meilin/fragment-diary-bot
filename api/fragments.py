"""
Fragment CRUD endpoints.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from api.deps import get_current_user
from models import Fragment, FragmentType
from services.supabase_client import get_db

router = APIRouter(prefix="/fragments", tags=["fragments"])


# ---- Schemas ----

class FragmentOut(BaseModel):
    id: str
    type: str
    content: str | None
    media_url: str | None
    created_at: str


class TodaySummary(BaseModel):
    count: int
    fragments: list[FragmentOut]


# ---- Endpoints ----

@router.post("/text")
async def create_text_fragment(
    content: str = Form(...),
    openid: str = Depends(get_current_user),
):
    """记录一条文字碎片."""
    db = get_db()
    fragment = Fragment(
        user_id=openid,
        type=FragmentType.TEXT,
        content=content,
    )
    saved = await db.save_fragment(fragment)
    return {"ok": True, "id": str(saved.id)}


@router.post("/photo")
async def create_photo_fragment(
    file: UploadFile = File(...),
    caption: str = Form(default=""),
    openid: str = Depends(get_current_user),
):
    """记录一条照片碎片 — 上传图片 + AI 描述."""
    db = get_db()

    # Upload to Supabase Storage
    file_bytes = await file.read()
    ext = file.filename.split(".")[-1] if file.filename else "jpg"
    storage_path = f"{openid}/photo/{uuid.uuid4()}.{ext}"
    media_url = await db.upload_file(storage_path, file_bytes, file.content_type or "image/jpeg")

    # AI describe
    description = caption
    try:
        from services.claude_service import get_claude
        claude = get_claude()
        description = await claude.describe_photo(media_url)
    except Exception:
        pass

    fragment = Fragment(
        user_id=openid,
        type=FragmentType.PHOTO,
        content=description or caption or "[照片]",
        media_url=media_url,
        metadata={"caption": caption},
    )
    saved = await db.save_fragment(fragment)
    return {"ok": True, "id": str(saved.id)}


@router.post("/voice")
async def create_voice_fragment(
    file: UploadFile = File(...),
    openid: str = Depends(get_current_user),
):
    """记录一条语音碎片."""
    db = get_db()

    file_bytes = await file.read()
    storage_path = f"{openid}/voice/{uuid.uuid4()}.mp3"
    media_url = await db.upload_file(storage_path, file_bytes, "audio/mpeg")

    # TODO: Whisper 语音转文字
    fragment = Fragment(
        user_id=openid,
        type=FragmentType.VOICE,
        content="[语音消息 — 待转录]",
        media_url=media_url,
        metadata={"filename": file.filename},
    )
    saved = await db.save_fragment(fragment)
    return {"ok": True, "id": str(saved.id)}


@router.get("/today", response_model=TodaySummary)
async def get_today_fragments(openid: str = Depends(get_current_user)):
    """获取今天的碎片列表."""
    db = get_db()
    fragments = await db.get_today_fragments(openid)

    return TodaySummary(
        count=len(fragments),
        fragments=[
            FragmentOut(
                id=str(f.id),
                type=f.type,
                content=f.content,
                media_url=f.media_url,
                created_at=f.created_at.isoformat() if f.created_at else "",
            )
            for f in fragments
        ],
    )


@router.delete("/{fragment_id}")
async def delete_fragment(
    fragment_id: str,
    openid: str = Depends(get_current_user),
):
    """删除一条碎片."""
    db = get_db()
    await db.delete_fragment(fragment_id, openid)
    return {"ok": True}
