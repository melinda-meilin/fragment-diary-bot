"""
Shared dependencies for API routes — auth extraction, DB access, etc.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Header

from config import Config
from api.auth import verify_token

config = Config.from_env()


async def get_current_user(authorization: str = Header(...)) -> str:
    """Extract and verify JWT from Authorization header, return openid."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = authorization[7:]
    openid = verify_token(token, config.jwt_secret)
    return openid
