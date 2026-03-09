"""
WeChat Mini Program authentication.

Flow:
1. 小程序端调用 wx.login() 拿到 code
2. 前端把 code 发到本接口
3. 后端用 code 换取 openid + session_key
4. 生成 JWT token 返回给前端
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import Config

router = APIRouter(prefix="/auth", tags=["auth"])

config = Config.from_env()

# ---- Schemas ----

class WxLoginRequest(BaseModel):
    code: str
    nickname: str | None = None
    avatar_url: str | None = None


class WxLoginResponse(BaseModel):
    token: str
    openid: str
    is_new_user: bool


# ---- JWT helpers (lightweight, no extra deps) ----

def _b64url(data: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def create_token(openid: str, secret: str, expires_hours: int = 168) -> str:
    """Create a simple HMAC-SHA256 JWT. 默认 7 天过期."""
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url(json.dumps({
        "openid": openid,
        "exp": int(time.time()) + expires_hours * 3600,
    }).encode())
    signature = _b64url(hmac.new(secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"


def verify_token(token: str, secret: str) -> str:
    """Verify JWT, return openid. Raises on failure."""
    import base64
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token format")

        # Verify signature
        expected_sig = _b64url(hmac.new(secret.encode(), f"{parts[0]}.{parts[1]}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(parts[2], expected_sig):
            raise ValueError("Invalid signature")

        # Decode payload
        padding = 4 - len(parts[1]) % 4
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * padding))

        if payload.get("exp", 0) < time.time():
            raise ValueError("Token expired")

        return payload["openid"]
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"认证失败: {e}")


# ---- Endpoints ----

@router.post("/login", response_model=WxLoginResponse)
async def wx_login(req: WxLoginRequest):
    """微信小程序登录 — 用 code 换取 openid."""

    # Call WeChat API: code → openid + session_key
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.weixin.qq.com/sns/jscode2session",
            params={
                "appid": config.wx_app_id,
                "secret": config.wx_app_secret,
                "js_code": req.code,
                "grant_type": "authorization_code",
            },
        )
    data = resp.json()

    if "openid" not in data:
        raise HTTPException(status_code=400, detail=f"微信登录失败: {data.get('errmsg', 'unknown')}")

    openid = data["openid"]

    # Upsert user in Supabase
    from services.supabase_client import get_db
    db = get_db()

    existing = await db.get_user(openid)
    is_new = existing is None

    from models import User
    user = User(
        id=openid,
        nickname=req.nickname,
        avatar_url=req.avatar_url,
    )
    await db.upsert_user(user)

    # Generate JWT
    token = create_token(openid, config.jwt_secret)

    return WxLoginResponse(token=token, openid=openid, is_new_user=is_new)
