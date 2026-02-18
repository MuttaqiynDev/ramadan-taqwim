import aiosqlite
import json
from typing import Any

class CacheRepo:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def get_daily(self, region_api: str, date_ymd: str) -> tuple[str, str] | None:
        cur = await self.db.execute(
            "SELECT suhoor, iftar FROM cache_daily WHERE region_api=? AND date=?",
            (region_api, date_ymd),
        )
        row = await cur.fetchone()
        if not row:
            return None
        return row["suhoor"], row["iftar"]

    async def set_daily(self, region_api: str, date_ymd: str, suhoor: str, iftar: str, raw: dict[str, Any]) -> None:
        await self.db.execute(
            """
            INSERT INTO cache_daily(region_api, date, suhoor, iftar, raw_json) VALUES(?,?,?,?,?)
            ON CONFLICT(region_api, date) DO UPDATE SET
              suhoor=excluded.suhoor,
              iftar=excluded.iftar,
              raw_json=excluded.raw_json,
              updated_at=CURRENT_TIMESTAMP
            """,
            (region_api, date_ymd, suhoor, iftar, json.dumps(raw, ensure_ascii=False)),
        )
        await self.db.commit()

    async def get_monthly_raw(self, region_api: str, ym: str) -> list[dict] | None:
        cur = await self.db.execute(
            "SELECT raw_json FROM cache_monthly WHERE region_api=? AND ym=?",
            (region_api, ym),
        )
        row = await cur.fetchone()
        if not row:
            return None
        return json.loads(row["raw_json"])

    async def set_monthly_raw(self, region_api: str, ym: str, raw_list: list[dict]) -> None:
        import json
        await self.db.execute(
            """
            INSERT INTO cache_monthly(region_api, ym, raw_json) VALUES(?,?,?)
            ON CONFLICT(region_api, ym) DO UPDATE SET raw_json=excluded.raw_json, updated_at=CURRENT_TIMESTAMP
            """,
            (region_api, ym, json.dumps(raw_list, ensure_ascii=False)),
        )
        await self.db.commit()
