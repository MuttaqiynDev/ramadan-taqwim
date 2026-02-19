import aiosqlite


class UsersRepo:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def ensure_columns(self):
        """Add reminder columns to existing databases safely."""
        try:
            await self.db.execute(
                "ALTER TABLE users ADD COLUMN reminder_enabled INTEGER DEFAULT 0"
            )
            await self.db.commit()
        except Exception:
            pass
        try:
            await self.db.execute(
                "ALTER TABLE users ADD COLUMN reminder_offset INTEGER DEFAULT 10"
            )
            await self.db.commit()
        except Exception:
            pass

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

    async def get_user(self, user_id: int) -> dict | None:
        cur = await self.db.execute(
            "SELECT user_id, region_code, reminder_enabled, reminder_offset FROM users WHERE user_id=?",
            (user_id,),
        )
        row = await cur.fetchone()
        if not row:
            return None
        return {
            "user_id": row["user_id"],
            "region_code": row["region_code"],
            "reminder_enabled": bool(row["reminder_enabled"]),
            "reminder_offset": row["reminder_offset"] or 10,
        }

    async def set_reminder(self, user_id: int, enabled: bool, offset: int = 10) -> None:
        await self.db.execute(
            """
            UPDATE users SET reminder_enabled=?, reminder_offset=?, updated_at=CURRENT_TIMESTAMP
            WHERE user_id=?
            """,
            (int(enabled), offset, user_id),
        )
        await self.db.commit()

    async def get_all_with_reminders(self) -> list[dict]:
        cur = await self.db.execute(
            "SELECT user_id, region_code, reminder_offset FROM users WHERE reminder_enabled=1 AND region_code IS NOT NULL"
        )
        rows = await cur.fetchall()
        return [
            {
                "user_id": row["user_id"],
                "region_code": row["region_code"],
                "reminder_offset": row["reminder_offset"] or 10,
            }
            for row in rows
        ]
