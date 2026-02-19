import asyncio
import aiohttp
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

from app.config import Config
from app.db.connection import init_db, get_db
from app.db.repo_users import UsersRepo
from app.db.repo_cache import CacheRepo
from app.handlers import start, region, menu
from app.services.islom_api import IslomApiClient
from app.services.reminders import setup_scheduler, schedule_all_reminders
from app.web.server import create_app

import uvicorn


async def run_bot(bot: Bot, dp: Dispatcher):
    """Run aiogram bot polling."""
    await dp.start_polling(bot)


async def run_webapp(fastapi_app, port: int):
    """Run FastAPI via uvicorn."""
    config = uvicorn.Config(
        fastapi_app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    cfg = Config()
    await init_db(cfg.db_path, "app/db/schema.sql")
    db = await get_db(cfg.db_path)

    users_repo = UsersRepo(db)
    cache_repo = CacheRepo(db)

    # Migrate existing databases (add new columns safely)
    await users_repo.ensure_columns()

    session = aiohttp.ClientSession()
    islom_client = IslomApiClient(session)

    bot_session = None
    if cfg.proxy_url:
        bot_session = AiohttpSession(proxy=cfg.proxy_url)

    bot = Bot(
        token=cfg.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=bot_session,
    )

    dp = Dispatcher()

    dp["cfg"] = cfg
    dp["db"] = db
    dp["users_repo"] = users_repo
    dp["cache_repo"] = cache_repo
    dp["islom_client"] = islom_client

    dp.include_router(start.router)
    dp.include_router(region.router)
    dp.include_router(menu.router)

    # Setup FastAPI app
    fastapi_app = create_app()
    fastapi_app.state.cfg = cfg
    fastapi_app.state.db = db
    fastapi_app.state.users_repo = users_repo
    fastapi_app.state.cache_repo = cache_repo
    fastapi_app.state.islom_client = islom_client
    fastapi_app.state.bot = bot

    # Setup APScheduler
    scheduler = setup_scheduler(bot, users_repo, cache_repo, islom_client, cfg)
    scheduler.start()
    fastapi_app.state.scheduler = scheduler

    # Schedule initial reminders
    try:
        await schedule_all_reminders(scheduler, bot, users_repo, cache_repo, islom_client, cfg)
    except Exception as e:
        logger.warning(f"Initial reminder scheduling failed (will retry at 00:05): {e}")

    logger.info(f"Starting bot + webapp on port {cfg.webapp_port}")
    logger.info(f"WebApp URL: {cfg.webapp_url}")

    try:
        await asyncio.gather(
            run_bot(bot, dp),
            run_webapp(fastapi_app, cfg.webapp_port),
        )
    finally:
        scheduler.shutdown(wait=False)
        await session.close()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
