from __future__ import annotations

from movievoter.database import Database


class MembershipRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def upsert_chat(
        self,
        chat_id: int,
        title: str | None = None,
        language: str | None = None,
    ) -> None:
        await self.db.execute(
            """
            INSERT INTO chats(chat_id, title, language)
            VALUES (?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                title = excluded.title,
                language = COALESCE(excluded.language, chats.language),
                status = 'active',
                updated_at = CURRENT_TIMESTAMP
            """,
            (chat_id, title, language),
        )

    async def upsert_member(
        self,
        chat_id: int,
        user_id: int,
        full_name: str,
        username: str | None = None,
        language: str | None = None,
    ) -> None:
        async with self.db.transaction() as conn:
            await conn.execute(
                """
                INSERT INTO users(tg_id, username, full_name, language)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(tg_id) DO UPDATE SET
                    username = excluded.username,
                    full_name = excluded.full_name,
                    language = COALESCE(excluded.language, users.language),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, username, full_name, language),
            )
            await conn.execute(
                """
                INSERT INTO chat_members(chat_id, user_id)
                VALUES (?, ?)
                ON CONFLICT(chat_id, user_id) DO UPDATE SET
                    last_seen_at = CURRENT_TIMESTAMP
                """,
                (chat_id, user_id),
            )

    async def is_member(self, chat_id: int, user_id: int) -> bool:
        row = await self.db.fetchone(
            "SELECT 1 FROM chat_members WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id),
        )
        return row is not None

    async def participant_count(self, chat_id: int) -> int:
        row = await self.db.fetchone(
            "SELECT COUNT(*) AS count FROM chat_members WHERE chat_id = ?",
            (chat_id,),
        )
        return int(row["count"]) if row else 0
