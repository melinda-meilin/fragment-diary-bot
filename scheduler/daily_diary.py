"""
Scheduler — runs daily diary synthesis for all users.
Diary will be stored in DB; user can pull it from the mini program.
"""

from __future__ import annotations

import logging
from datetime import date

from models import Diary
from services.supabase_client import SupabaseService
from services.claude_service import DiaryAIService as ClaudeService

logger = logging.getLogger(__name__)


async def generate_daily_diaries(
    db: SupabaseService,
    claude: ClaudeService,
):
    """Generate diary for every active user, called by APScheduler."""
    logger.info("🌙 Starting daily diary generation...")

    user_ids = await db.get_all_user_ids()
    today = date.today()
    generated = 0

    for user_id in user_ids:
        try:
            fragments = await db.get_today_fragments(user_id)
            if not fragments:
                continue

            existing = await db.get_diary(user_id, today)
            if existing:
                continue

            diary_text = await claude.synthesize_diary(fragments, today)

            diary = Diary(
                user_id=user_id,
                diary_date=today,
                content=diary_text,
                fragment_ids=[f.id for f in fragments if f.id],
            )
            await db.save_diary(diary)
            generated += 1

            # TODO: 可以接入微信模板消息推送提醒用户查看日记

            logger.info(f"User {user_id[:8]}...: diary generated ✓")

        except Exception as e:
            logger.error(f"User {user_id[:8]}...: diary generation failed — {e}")

    logger.info(f"🌙 Daily diary generation complete. Generated {generated} diaries.")
