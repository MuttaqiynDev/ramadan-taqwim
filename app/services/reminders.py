"""APScheduler-based reminder service for iftar time notifications."""
from __future__ import annotations
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from app.services.dates import _get_tz, today as get_today
from app.services.data_service import get_suhoor_iftar
from app.services.regions import get_region_by_code

logger = logging.getLogger(__name__)


async def send_reminder(bot, user_id: int, iftar_time: str, region_title: str):
    """Send a reminder message to the user."""
    try:
        await bot.send_message(
            user_id,
            f"🔔 <b>Eslatma!</b>\n\n"
            f"📍 {region_title}\n"
            f"🌅 Iftorlik vaqti: <b>{iftar_time}</b>\n\n"
            f"Iftor vaqti yaqinlashdi! Tayyorlaning.\n"
            f"@MuttaqiynDevbot",
        )
    except Exception as e:
        logger.warning(f"Could not send reminder to {user_id}: {e}")


async def schedule_all_reminders(scheduler, bot, users_repo, cache_repo, islom_client, cfg):
    """Schedule reminders for all users with reminders enabled."""
    # Remove all existing reminder jobs
    for job in scheduler.get_jobs():
        if job.id.startswith("reminder_"):
            job.remove()

    users = await users_repo.get_all_with_reminders()
    tz_obj = _get_tz(cfg.tz)
    d = get_today(cfg.tz)

    for user in users:
        try:
            reg = get_region_by_code(user["region_code"])
            if not reg:
                continue

            _, iftar = await get_suhoor_iftar(
                cache_repo, islom_client, reg.api_name, d
            )

            offset = user.get("reminder_offset", 10)
            iftar_dt = datetime.strptime(iftar, "%H:%M").replace(
                year=d.year, month=d.month, day=d.day, tzinfo=tz_obj
            )
            remind_dt = iftar_dt - timedelta(minutes=offset)

            now = datetime.now(tz_obj)
            if remind_dt > now:
                scheduler.add_job(
                    send_reminder,
                    trigger=DateTrigger(run_date=remind_dt),
                    args=[bot, user["user_id"], iftar, reg.title],
                    id=f"reminder_{user['user_id']}",
                    replace_existing=True,
                )
                logger.info(f"Scheduled reminder for user {user['user_id']} at {remind_dt}")
        except Exception as e:
            logger.warning(f"Failed to schedule reminder for user {user['user_id']}: {e}")


async def reschedule_user(scheduler, bot, users_repo, cache_repo, islom_client, cfg, user_id: int):
    """Reschedule reminder for a specific user (called when they toggle reminder)."""
    # Remove existing
    job_id = f"reminder_{user_id}"
    try:
        job = scheduler.get_job(job_id)
        if job:
            job.remove()
    except Exception:
        pass

    user = await users_repo.get_user(user_id)
    if not user or not user["reminder_enabled"] or not user["region_code"]:
        return

    reg = get_region_by_code(user["region_code"])
    if not reg:
        return

    tz_obj = _get_tz(cfg.tz)
    d = get_today(cfg.tz)

    try:
        _, iftar = await get_suhoor_iftar(
            cache_repo, islom_client, reg.api_name, d
        )
        offset = user.get("reminder_offset", 10)
        iftar_dt = datetime.strptime(iftar, "%H:%M").replace(
            year=d.year, month=d.month, day=d.day, tzinfo=tz_obj
        )
        remind_dt = iftar_dt - timedelta(minutes=offset)

        now = datetime.now(tz_obj)
        if remind_dt > now:
            scheduler.add_job(
                send_reminder,
                trigger=DateTrigger(run_date=remind_dt),
                args=[bot, user_id, iftar, reg.title],
                id=job_id,
                replace_existing=True,
            )
    except Exception as e:
        logger.warning(f"Failed to reschedule reminder for user {user_id}: {e}")


def setup_scheduler(bot, users_repo, cache_repo, islom_client, cfg) -> AsyncIOScheduler:
    """Create and configure the scheduler."""
    scheduler = AsyncIOScheduler()

    # Daily refresh at 00:05
    scheduler.add_job(
        schedule_all_reminders,
        trigger=CronTrigger(hour=0, minute=5),
        args=[scheduler, bot, users_repo, cache_repo, islom_client, cfg],
        id="daily_refresh",
        replace_existing=True,
    )

    return scheduler
