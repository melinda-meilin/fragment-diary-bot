"""
Fragment Diary — FastAPI server entry point.

Usage:
    python main.py
    # or: uvicorn main:app --reload
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import Config
from services.supabase_client import get_db
from services.claude_service import get_claude
from scheduler.daily_diary import generate_daily_diaries
from utils.logger import setup_logging

from api.auth import router as auth_router
from api.fragments import router as fragments_router
from api.diaries import router as diaries_router

logger = logging.getLogger(__name__)

config = Config.from_env()


# ---- Lifecycle ----

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    setup_logging()

    # Warm up singletons
    get_db()
    get_claude()
    logger.info("Services initialized ✓")

    # Start scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        generate_daily_diaries,
        trigger=CronTrigger(
            hour=config.diary_hour,
            minute=config.diary_minute,
            timezone=config.timezone,
        ),
        kwargs={"db": get_db(), "claude": get_claude()},
        id="daily_diary",
        name="Daily diary generation",
    )
    scheduler.start()
    logger.info(
        f"Scheduler started — diary at "
        f"{config.diary_hour:02d}:{config.diary_minute:02d} ({config.timezone}) ✓"
    )

    logger.info("🚀 Server is running!")
    yield

    scheduler.shutdown()
    logger.info("Server stopped.")


# ---- App ----

app = FastAPI(
    title="碎片日记 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,      prefix="/api")
app.include_router(fragments_router, prefix="/api")
app.include_router(diaries_router,   prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host=config.host, port=config.port, reload=True)
