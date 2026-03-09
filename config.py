"""
Application configuration — loaded from environment variables.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # WeChat Mini Program
    wx_app_id: str = ""
    wx_app_secret: str = ""

    # JWT
    jwt_secret: str = "change-me-to-a-random-string"

    # Claude API
    claude_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""

    # Scheduler — 每天几点生成日记 (24h format, 当地时区)
    diary_hour: int = 22
    diary_minute: int = 0
    timezone: str = "Asia/Shanghai"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            wx_app_id=os.environ.get("WX_APP_ID", ""),
            wx_app_secret=os.environ.get("WX_APP_SECRET", ""),
            jwt_secret=os.environ.get("JWT_SECRET", cls.jwt_secret),
            claude_api_key=os.environ.get("CLAUDE_API_KEY", ""),
            claude_model=os.environ.get("CLAUDE_MODEL", cls.claude_model),
            supabase_url=os.environ["SUPABASE_URL"],
            supabase_key=os.environ["SUPABASE_KEY"],
            diary_hour=int(os.environ.get("DIARY_HOUR", cls.diary_hour)),
            diary_minute=int(os.environ.get("DIARY_MINUTE", cls.diary_minute)),
            timezone=os.environ.get("TIMEZONE", cls.timezone),
            host=os.environ.get("HOST", cls.host),
            port=int(os.environ.get("PORT", cls.port)),
        )
