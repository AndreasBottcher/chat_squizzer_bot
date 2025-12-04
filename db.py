from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import aiosqlite

from config import DB_PATH, logger


async def init_db():
    """Initialize the database and create tables if they don't exist"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                username TEXT NOT NULL,
                text TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_timestamp
            ON messages(chat_id, timestamp)
        """)
        await db.commit()
        logger.info("Database initialized")


async def add_message(
    chat_id: int, username: str, text: str, timestamp: Optional[datetime] = None
):
    """Add a message to the database"""
    if timestamp is None:
        timestamp = datetime.now()

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (chat_id, timestamp, username, text) VALUES (?, ?, ?, ?)",
            (chat_id, timestamp.isoformat(), username, text),
        )
        await db.commit()


async def get_messages_period(
    chat_id: int, hours: int
) -> List[Tuple[datetime, str, str]]:
    """Get all messages from the last N hours for a chat"""
    cutoff_time = datetime.now() - timedelta(hours=hours)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT timestamp, username, text FROM messages WHERE chat_id = ? AND timestamp > ? ORDER BY timestamp",
            (chat_id, cutoff_time.isoformat()),
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                (datetime.fromisoformat(row["timestamp"]), row["username"], row["text"])
                for row in rows
            ]


async def clean_old_messages(hours: int):
    """Remove messages older than N hours from storage"""
    cutoff_time = datetime.now() - timedelta(hours=hours)

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM messages WHERE timestamp < ?", (cutoff_time.isoformat(),)
        )
        deleted_count = cursor.rowcount
        await db.commit()
        if deleted_count > 0:
            logger.info(f"Cleaned {deleted_count} old messages from database")


async def clear_chat_messages(chat_id: int):
    """Clear all messages for a specific chat"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        deleted_count = cursor.rowcount
        await db.commit()
        logger.info(f"Cleared {deleted_count} messages for chat {chat_id}")
        return deleted_count


async def get_message_count(chat_id: int, hours: int) -> int:
    """Get the count of messages for a chat in the last N hours"""
    cutoff_time = datetime.now() - timedelta(hours=hours)

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) as count FROM messages WHERE chat_id = ? AND timestamp > ?",
            (chat_id, cutoff_time.isoformat()),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0
