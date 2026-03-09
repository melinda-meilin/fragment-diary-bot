"""
Telegram Bot handlers — receives user fragments and commands.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import date

from telegram import Update
from telegram.ext import ContextTypes

from models import Fragment, FragmentType, User
from services.supabase_client import SupabaseService
from services.claude_service import ClaudeService

logger = logging.getLogger(__name__)


class BotHandlers:
    def __init__(self, db: SupabaseService, claude: ClaudeService, temp_dir: str):
        self.db = db
        self.claude = claude
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)

    # ---- Commands ----

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start — register user."""
        tg_user = update.effective_user
        user = User(
            id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
        )
        await self.db.upsert_user(user)

        await update.message.reply_text(
            "✨ 欢迎使用碎片日记！\n\n"
            "随时发给我文字、语音或照片，我会帮你收集生活碎片。\n"
            "每天晚上我会自动把碎片整合成一篇完整的日记 📖\n\n"
            "指令：\n"
            "/today — 查看今天收集的碎片\n"
            "/diary — 立即生成今天的日记\n"
            "/history — 查看最近 7 天日记"
        )

    async def cmd_today(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show today's collected fragments."""
        user_id = update.effective_user.id
        fragments = await self.db.get_today_fragments(user_id)

        if not fragments:
            await update.message.reply_text("今天还没有碎片哦，发点什么给我吧 ✏️")
            return

        lines = [f"📋 今天已收集 {len(fragments)} 个碎片：\n"]
        for i, f in enumerate(fragments, 1):
            time_str = f.created_at.strftime("%H:%M") if f.created_at else ""
            tag = {"text": "📝", "voice": "🎙️", "photo": "📷"}.get(f.type, "💬")
            preview = (f.content[:50] + "...") if f.content and len(f.content) > 50 else (f.content or "")
            lines.append(f"{i}. {tag} {time_str} {preview}")

        await update.message.reply_text("\n".join(lines))

    async def cmd_diary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manually trigger diary generation for today."""
        user_id = update.effective_user.id
        fragments = await self.db.get_today_fragments(user_id)

        if not fragments:
            await update.message.reply_text("今天还没有碎片，无法生成日记 😅")
            return

        await update.message.reply_text("🖊️ 正在为你撰写今天的日记，请稍候...")

        diary_text = await self.claude.synthesize_diary(fragments, date.today())

        from models import Diary

        diary = Diary(
            user_id=user_id,
            diary_date=date.today(),
            content=diary_text,
            fragment_ids=[f.id for f in fragments if f.id],
        )
        await self.db.save_diary(diary)

        await update.message.reply_text(diary_text, parse_mode="Markdown")

    async def cmd_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show recent diary entries."""
        user_id = update.effective_user.id
        diaries = await self.db.get_recent_diaries(user_id, days=7)

        if not diaries:
            await update.message.reply_text("还没有生成过日记哦 📭")
            return

        for d in diaries:
            header = f"📖 {d.diary_date.isoformat()}\n\n"
            # Telegram has a 4096 char limit per message
            text = header + d.content
            if len(text) > 4000:
                text = text[:4000] + "\n\n...(已截断)"
            await update.message.reply_text(text, parse_mode="Markdown")

    # ---- Fragment Receivers ----

    async def on_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save a text fragment."""
        fragment = Fragment(
            user_id=update.effective_user.id,
            type=FragmentType.TEXT,
            content=update.message.text,
        )
        saved = await self.db.save_fragment(fragment)
        await update.message.reply_text("📝 碎片已记录 ✓")

    async def on_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save a voice fragment — download, upload to storage, transcribe later."""
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)

        # Download voice to temp
        local_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}.ogg")
        await file.download_to_drive(local_path)

        # Upload to Supabase Storage
        with open(local_path, "rb") as f:
            file_bytes = f.read()

        storage_path = f"{update.effective_user.id}/voice/{uuid.uuid4()}.ogg"
        media_url = await self.db.upload_file(storage_path, file_bytes, "audio/ogg")

        # TODO: integrate a speech-to-text service (Whisper API, etc.)
        # For now, store with placeholder content
        fragment = Fragment(
            user_id=update.effective_user.id,
            type=FragmentType.VOICE,
            content="[语音消息 — 待转录]",
            media_url=media_url,
            metadata={"duration": voice.duration},
        )
        saved = await self.db.save_fragment(fragment)
        await update.message.reply_text("🎙️ 语音碎片已记录 ✓")

        # Cleanup
        os.remove(local_path)

    async def on_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save a photo fragment — download, upload, get AI description."""
        photo = update.message.photo[-1]  # highest resolution
        file = await context.bot.get_file(photo.file_id)

        local_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}.jpg")
        await file.download_to_drive(local_path)

        with open(local_path, "rb") as f:
            file_bytes = f.read()

        storage_path = f"{update.effective_user.id}/photo/{uuid.uuid4()}.jpg"
        media_url = await self.db.upload_file(storage_path, file_bytes, "image/jpeg")

        # Use Claude vision to describe the photo
        try:
            description = await self.claude.describe_photo(media_url)
        except Exception as e:
            logger.warning(f"Photo description failed: {e}")
            description = update.message.caption or "[照片]"

        fragment = Fragment(
            user_id=update.effective_user.id,
            type=FragmentType.PHOTO,
            content=description,
            media_url=media_url,
            metadata={"caption": update.message.caption},
        )
        saved = await self.db.save_fragment(fragment)
        await update.message.reply_text("📷 照片碎片已记录 ✓")

        os.remove(local_path)
