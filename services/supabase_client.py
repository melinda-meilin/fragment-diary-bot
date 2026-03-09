"""
Supabase service — handles all DB reads/writes and file storage.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from uuid import UUID

from supabase import create_client, Client

from config import Config
from models import Fragment, Diary, User

logger = logging.getLogger(__name__)

# Singleton instance
_instance: SupabaseService | None = None


def get_db() -> SupabaseService:
    global _instance
    if _instance is None:
        _instance = SupabaseService(Config.from_env())
    return _instance


class SupabaseService:
    def __init__(self, config: Config):
        self.client: Client = create_client(config.supabase_url, config.supabase_key)

    # ---- Users ----

    async def upsert_user(self, user: User) -> None:
        self.client.table("users").upsert(user.model_dump()).execute()

    async def get_user(self, openid: str) -> User | None:
        result = self.client.table("users").select("*").eq("id", openid).execute()
        if result.data:
            return User(**result.data[0])
        return None

    # ---- Fragments ----

    async def save_fragment(self, fragment: Fragment) -> Fragment:
        data = fragment.model_dump(exclude_none=True, mode="json")
        result = self.client.table("fragments").insert(data).execute()
        return Fragment(**result.data[0])

    async def get_today_fragments(
        self, user_id: str, tz_offset_hours: int = 8
    ) -> list[Fragment]:
        """Fetch all fragments from today (user's local timezone)."""
        now = datetime.utcnow() + timedelta(hours=tz_offset_hours)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(hours=tz_offset_hours)
        end_of_day = start_of_day + timedelta(days=1)

        result = (
            self.client.table("fragments")
            .select("*")
            .eq("user_id", user_id)
            .gte("created_at", start_of_day.isoformat())
            .lt("created_at", end_of_day.isoformat())
            .order("created_at")
            .execute()
        )
        return [Fragment(**row) for row in result.data]

    async def get_fragments_by_date(
        self, user_id: str, target_date: date, tz_offset_hours: int = 8
    ) -> list[Fragment]:
        start = datetime(target_date.year, target_date.month, target_date.day) - timedelta(hours=tz_offset_hours)
        end = start + timedelta(days=1)

        result = (
            self.client.table("fragments")
            .select("*")
            .eq("user_id", user_id)
            .gte("created_at", start.isoformat())
            .lt("created_at", end.isoformat())
            .order("created_at")
            .execute()
        )
        return [Fragment(**row) for row in result.data]

    async def delete_fragment(self, fragment_id: str, user_id: str) -> None:
        self.client.table("fragments").delete().eq("id", fragment_id).eq("user_id", user_id).execute()

    # ---- Diaries ----

    async def save_diary(self, diary: Diary) -> Diary:
        data = diary.model_dump(exclude_none=True, mode="json")
        result = self.client.table("diaries").upsert(data).execute()
        return Diary(**result.data[0])

    async def get_diary(self, user_id: str, diary_date: date) -> Diary | None:
        result = (
            self.client.table("diaries")
            .select("*")
            .eq("user_id", user_id)
            .eq("diary_date", diary_date.isoformat())
            .execute()
        )
        if result.data:
            return Diary(**result.data[0])
        return None

    async def get_recent_diaries(self, user_id: str, days: int = 30) -> list[Diary]:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        result = (
            self.client.table("diaries")
            .select("*")
            .eq("user_id", user_id)
            .gte("diary_date", cutoff)
            .order("diary_date", desc=True)
            .execute()
        )
        return [Diary(**row) for row in result.data]

    # ---- File Storage ----

    async def upload_file(self, path: str, file_bytes: bytes, content_type: str) -> str:
        self.client.storage.from_("fragments").upload(
            path, file_bytes, {"content-type": content_type}
        )
        return self.client.storage.from_("fragments").get_public_url(path)

    # ---- Utils ----

    async def get_all_user_ids(self) -> list[str]:
        result = self.client.table("users").select("id").execute()
        return [row["id"] for row in result.data]
