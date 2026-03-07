"""Main bot entry point — setup, polling, auto-close worker."""

import asyncio
import logging
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, AUTO_CLOSE_HOURS, SUPPORT_GROUP_ID
import db
from i18n import t
from handlers import user as user_handlers
from handlers import group as group_handlers

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── Auto-close worker ─────────────────────────────────────────────────────────

async def auto_close_worker(bot: Bot):
    """Background task: close stale tickets every hour."""
    while True:
        try:
            stale_tickets = await db.get_stale_tickets(hours=AUTO_CLOSE_HOURS)
            for ticket in stale_tickets:
                ticket_id = ticket["id"]
                lang = ticket.get("language", "ru")
                print(f"[AUTO-CLOSE] Closing stale ticket #{ticket_id} (last activity: {ticket['updated_at']})")

                await db.set_ticket_status(ticket_id, "closed_auto")

                # Notify user
                try:
                    await bot.send_message(
                        chat_id=ticket["telegram_id"],
                        text=t(lang, "auto_closed", id=ticket_id),
                        parse_mode="HTML",
                    )
                except Exception as e:
                    print(f"[WARN] Could not notify user {ticket['telegram_id']} for auto-close: {e}")

                # Close forum topic
                if ticket.get("topic_id"):
                    try:
                        await bot.close_forum_topic(
                            chat_id=SUPPORT_GROUP_ID,
                            message_thread_id=ticket["topic_id"],
                        )
                    except Exception as e:
                        print(f"[WARN] Could not close forum topic {ticket['topic_id']}: {e}")

        except Exception as e:
            print(f"[ERROR] Auto-close worker error: {e}")

        # Sleep 1 hour
        await asyncio.sleep(3600)


# ── Startup / Shutdown ────────────────────────────────────────────────────────

async def on_startup(bot: Bot):
    """Initialize DB and print bot info on startup."""
    await db.init_db()
    bot_info = await bot.get_me()
    print(f"[BOT] Started: @{bot_info.username} (id={bot_info.id})")
    print(f"[BOT] Support group: {SUPPORT_GROUP_ID}")
    print(f"[BOT] Auto-close after: {AUTO_CLOSE_HOURS}h")


async def on_shutdown(bot: Bot):
    print("[BOT] Shutting down...")
    await bot.session.close()


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register routers
    dp.include_router(user_handlers.router)
    dp.include_router(group_handlers.router)

    # Startup hook
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Start auto-close worker as background task
    asyncio.create_task(auto_close_worker(bot))

    print("[BOT] Starting polling...")
    await dp.start_polling(
        bot,
        allowed_updates=["message", "callback_query", "my_chat_member"],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
