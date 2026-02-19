from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    bot_token: str = os.environ["BOT_TOKEN"]
    db_path: str = os.getenv("DB_PATH", "./bot.db")
    tz: str = os.getenv("TZ", "Asia/Tashkent")

    ramadan_start: str = os.getenv("RAMADAN_START", "2026-02-18")
    ramadan_days: int = int(os.getenv("RAMADAN_DAYS", "30"))

    proxy_url: str | None = os.getenv("PROXY_URL")

    webapp_url: str = os.getenv("WEBAPP_URL", "http://localhost:8000/webapp")
    base_url: str = os.getenv("BASE_URL", "http://localhost:8000")
    webapp_port: int = int(os.getenv("WEBAPP_PORT", "8000"))
