#!/usr/bin/env python3

import asyncio
import contextlib
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings
from telegram import Bot

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    CHAT_ID: int = Field(default=...)
    TELEGRAM_TOKEN: str = Field(default=...)
    HOURS: int = Field(default=...)
    MINUTES: int = Field(default=...)


async def remind_pranzo_tomorrow(bot: Bot, chat_id: str) -> None:
    """Handler to send to chat message for pranzo tomorrow."""
    try:
        await bot.send_poll(
            chat_id=chat_id,
            question="Chi mangia in ufficio domani? 🍝",
            options=["Io", "Non io"],
            disable_notification=True,
            allows_multiple_answers=False,
        )
    except Exception as e:
        logger.error(f"Error sending message: {e}")


async def main():
    load_dotenv()
    settings = Settings()
    scheduler = AsyncIOScheduler()
    logger.info("Settings loaded, starting bot...")

    # Run the bot indefinitely.
    async with Bot(settings.TELEGRAM_TOKEN) as bot:
        scheduler.add_job(
            remind_pranzo_tomorrow,
            kwargs={"bot": bot, "chat_id": settings.CHAT_ID},
            trigger="cron",
            hour=settings.HOURS,
            minute=settings.MINUTES,
            timezone="Europe/Rome",
            day_of_week="mon-fri",
        )
        scheduler.start()
        while True:
            await asyncio.sleep(1000)


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
