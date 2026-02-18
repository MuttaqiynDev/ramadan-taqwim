import aiosqlite

class UsersRepo:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def get_region_code(self, user_id: int) -> str | None:
        cur = await self.db.execute("SELECT region_code FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return row["region_code"] if row else None

    async def set_region_code(self, user_id: int, region_code: str) -> None:
        await self.db.execute(
            """
            INSERT INTO users(user_id, region_code) VALUES(?, ?)
            ON CONFLICT(user_id) DO UPDATE SET region_code=excluded.region_code, updated_at=CURRENT_TIMESTAMP
            """,
            (user_id, region_code),
        )
        await self.db.commit()
