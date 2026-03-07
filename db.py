"""SQLite database operations using aiosqlite."""

import aiosqlite
from datetime import datetime, timezone
from config import DB_PATH

CREATE_TICKETS = """
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    username TEXT,
    language TEXT DEFAULT 'ru',
    topic_id INTEGER,
    status TEXT DEFAULT 'open',
    subject TEXT,
    rating INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);
"""

CREATE_MESSAGES = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    sender TEXT NOT NULL,
    text TEXT,
    message_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_FAQ_STATS = """
CREATE TABLE IF NOT EXISTS faq_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    helped BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


async def init_db():
    """Initialize database schema."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_TICKETS)
        await db.execute(CREATE_MESSAGES)
        await db.execute(CREATE_FAQ_STATS)
        await db.commit()
    print(f"[DB] Database initialized at {DB_PATH}")


async def create_ticket(telegram_id: int, username: str | None, language: str, subject: str) -> int:
    """Create a new ticket and return its ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO tickets (telegram_id, username, language, subject, status) VALUES (?, ?, ?, ?, 'open')",
            (telegram_id, username, language, subject),
        )
        await db.commit()
        return cursor.lastrowid


async def update_ticket_topic(ticket_id: int, topic_id: int):
    """Set the forum topic_id for a ticket."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tickets SET topic_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (topic_id, ticket_id),
        )
        await db.commit()


async def get_ticket_by_id(ticket_id: int) -> dict | None:
    """Get ticket by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_open_ticket_for_user(telegram_id: int) -> dict | None:
    """Get the user's open (or waiting_user) ticket."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tickets WHERE telegram_id = ? AND status IN ('open', 'waiting_user') ORDER BY created_at DESC LIMIT 1",
            (telegram_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_ticket_by_topic(topic_id: int) -> dict | None:
    """Find ticket by its forum topic_id."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tickets WHERE topic_id = ? AND status IN ('open', 'waiting_user') ORDER BY created_at DESC LIMIT 1",
            (topic_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def set_ticket_status(ticket_id: int, status: str):
    """Update ticket status."""
    resolved_at_sql = ""
    params = [status, ticket_id]
    if status in ("resolved", "closed_auto"):
        resolved_at_sql = ", resolved_at = CURRENT_TIMESTAMP"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE tickets SET status = ?, updated_at = CURRENT_TIMESTAMP{resolved_at_sql} WHERE id = ?",
            params,
        )
        await db.commit()


async def set_ticket_rating(ticket_id: int, rating: int):
    """Save user rating for a ticket."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tickets SET rating = ? WHERE id = ?",
            (rating, ticket_id),
        )
        await db.commit()


async def update_ticket_activity(ticket_id: int):
    """Touch updated_at to prevent auto-close."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tickets SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (ticket_id,),
        )
        await db.commit()


async def add_message(ticket_id: int, sender: str, text: str | None, message_id: int | None):
    """Log a message to the messages table."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (ticket_id, sender, text, message_id) VALUES (?, ?, ?, ?)",
            (ticket_id, sender, text, message_id),
        )
        await db.commit()


async def get_stale_tickets(hours: int = 48) -> list[dict]:
    """Get tickets that haven't been updated in `hours` hours."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM tickets
            WHERE status IN ('open', 'waiting_user')
              AND updated_at < datetime('now', ? || ' hours')
            """,
            (f"-{hours}",),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def log_faq_stat(category: str, helped: bool):
    """Record whether a FAQ answer helped the user."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO faq_stats (category, helped) VALUES (?, ?)",
            (category, helped),
        )
        await db.commit()
