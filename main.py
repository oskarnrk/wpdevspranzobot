#!/usr/bin/env python3

import asyncio
import contextlib
import holidays
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import date
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings
from telegram import Bot

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    CHAT_ID: int = Field(default=...)
    TELEGRAM_TOKEN: str = Field(default=...)
    HOURS: int = Field(default=...)
    MINUTES: int = Field(default=...)
    IT_PROVINCE: str = Field(default=None)
    CUSTOM_SKIP_DATES: str = Field(default=None)


async def remind_pranzo_tomorrow(bot: Bot, chat_id: str) -> None:
    """Handler to send to chat message for pranzo tomorrow."""

    # Check if tomorrow is a holiday in Italy (in the specified province if set)
    # Province codes can be found at https://holidays.readthedocs.io/en/latest/
    if settings.IT_PROVINCE:
        skip_dates = holidays.IT(prov=settings.IT_PROVINCE)
    else:
        skip_dates = holidays.IT()

    # Add custom skip dates if provided
    if settings.CUSTOM_SKIP_DATES: # dates in format "%m-%d"
        custom_skip_dates = settings.CUSTOM_SKIP_DATES.split(",")
        for date_str in custom_skip_dates:
            day, month = map(int, date_str.split("-"))
            custom_date = date(year=date.today().year, month=month, day=day)
            skip_dates.append(custom_date.strftime("%d-%m-%Y"))

    tomorrow = (await bot.get_me()).date + timedelta(days=1)
    if tomorrow in skip_dates:
        logger.info("Tomorrow is in the skip days list, not sending poll.")
        return

    try:
        await bot.send_poll(
            chat_id=chat_id,
            question="Dove mangerai domani? 🍝",
            options=["Ufficio", "Mensa", "Home office", "Ferie/permesso"],
            disable_notification=True,
            allows_multiple_answers=False,
            is_anonymous=False,
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
            day_of_week="sun,mon,tue,wed,thu",
        )
        scheduler.start()
        while True:
            await asyncio.sleep(1000)


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
