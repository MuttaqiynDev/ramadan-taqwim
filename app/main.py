import asyncio
import aiohttp
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from app.config import Config
from app.db.connection import init_db, get_db
from app.db.repo_users import UsersRepo
from app.db.repo_cache import CacheRepo
from app.handlers import start, region, menu
from app.services.islom_api import IslomApiClient
from aiogram.client.session.aiohttp import AiohttpSession

async def main():
    logging.basicConfig(level=logging.INFO)

    cfg = Config()
    await init_db(cfg.db_path, "app/db/schema.sql")
    db = await get_db(cfg.db_path)

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

    # ✅ dependencies (workflow_data)
    dp["cfg"] = cfg
    dp["db"] = db
    dp["users_repo"] = UsersRepo(db)
    dp["cache_repo"] = CacheRepo(db)
    dp["islom_client"] = islom_client

    dp.include_router(start.router)
    dp.include_router(region.router)
    dp.include_router(menu.router)

    try:
        await dp.start_polling(bot)
    finally:
        await session.close()
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())
