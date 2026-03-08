"""Group handlers — support replies, ticket control buttons."""

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import db
from i18n import t
from config import SUPPORT_GROUP_ID

router = Router()


# ── Helper: forward support message to user ───────────────────────────────────

async def _forward_support_to_user(bot: Bot, message: Message, ticket: dict):
    """Forward a support message from group topic to the user in DM."""
    user_id = ticket["telegram_id"]
    footer = "— DuckSurf Support"

    try:
        if message.text:
            await bot.send_message(
                chat_id=user_id,
                text=f"{message.text}\n\n{footer}",
            )
        elif message.photo:
            await bot.send_photo(
                chat_id=user_id,
                photo=message.photo[-1].file_id,
                caption=f"{message.caption or ''}\n\n{footer}",
            )
        elif message.video:
            await bot.send_video(
                chat_id=user_id,
                video=message.video.file_id,
                caption=f"{message.caption or ''}\n\n{footer}",
            )
        elif message.document:
            await bot.send_document(
                chat_id=user_id,
                document=message.document.file_id,
                caption=f"{message.caption or ''}\n\n{footer}",
            )
        elif message.voice:
            await bot.send_voice(
                chat_id=user_id,
                voice=message.voice.file_id,
            )
            # Send footer as separate message for voice
            await bot.send_message(chat_id=user_id, text=footer)
        elif message.video_note:
            await bot.send_video_note(
                chat_id=user_id,
                video_note=message.video_note.file_id,
            )
            await bot.send_message(chat_id=user_id, text=footer)
        elif message.audio:
            await bot.send_audio(
                chat_id=user_id,
                audio=message.audio.file_id,
                caption=f"{message.caption or ''}\n\n{footer}",
            )
        elif message.sticker:
            await bot.send_sticker(
                chat_id=user_id,
                sticker=message.sticker.file_id,
            )
            await bot.send_message(chat_id=user_id, text=footer)
        else:
            # Fallback for unsupported types
            await bot.send_message(
                chat_id=user_id,
                text=f"[Медиа от поддержки]\n\n{footer}",
            )
    except Exception as e:
        print(f"[ERROR] Failed to forward support message to user {user_id}: {e}")
        raise


# ── Group message handler ─────────────────────────────────────────────────────

@router.message(F.chat.id == SUPPORT_GROUP_ID, F.chat.type.in_({"group", "supergroup"}), F.from_user)
async def handle_group_message(message: Message, bot: Bot):
    """Handle messages in the support group topics → forward to user DM."""
    # Skip messages not in a topic thread
    if not message.message_thread_id:
        return

    # Skip bot's own messages
    if message.from_user.id == bot.id:
        return

    # Skip service/system messages (topic created, pinned, etc.)
    if not any([message.text, message.photo, message.video, message.document,
                message.voice, message.video_note, message.audio, message.sticker]):
        return

    topic_id = message.message_thread_id

    # Find ticket by topic
    ticket = await db.get_ticket_by_topic(topic_id)
    if not ticket:
        # No active ticket for this topic — ignore
        return

    # Forward to user
    try:
        await _forward_support_to_user(bot, message, ticket)
        raw_text = message.text or message.caption or ""
        await db.add_message(ticket["id"], "support", raw_text or "[media]", message.message_id)
        await db.update_ticket_activity(ticket["id"])
        print(f"[GROUP] Forwarded support message from topic {topic_id} to user {ticket['telegram_id']}")
    except Exception as e:
        print(f"[ERROR] Error handling group message for ticket #{ticket['id']}: {e}")


# ── Ticket control callbacks ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("close_ticket_"))
async def handle_close_ticket(callback: CallbackQuery, bot: Bot):
    """Support closes a ticket."""
    ticket_id = int(callback.data.split("_")[2])
    ticket = await db.get_ticket_by_id(ticket_id)

    if not ticket:
        await callback.answer("Тикет не найден.", show_alert=True)
        return

    if ticket["status"] in ("resolved", "closed_auto"):
        await callback.answer("Тикет уже закрыт.", show_alert=True)
        return

    # Update status
    await db.set_ticket_status(ticket_id, "resolved")

    # Update the info card buttons (disable them)
    try:
        await callback.message.edit_reply_markup(
            reply_markup=_closed_keyboard(ticket_id)
        )
    except Exception as e:
        print(f"[WARN] Could not edit info card buttons: {e}")

    # Notify user
    lang = ticket.get("language", "ru")
    try:
        await bot.send_message(
            chat_id=ticket["telegram_id"],
            text=t(lang, "ticket_resolved", id=ticket_id),
            parse_mode="HTML",
        )
        # Send rating keyboard
        from handlers.user import rating_keyboard
        await bot.send_message(
            chat_id=ticket["telegram_id"],
            text=t(lang, "rate_support"),
            reply_markup=rating_keyboard(ticket_id),
            parse_mode="HTML",
        )
    except Exception as e:
        print(f"[WARN] Could not notify user {ticket['telegram_id']} about resolution: {e}")

    # Close the forum topic
    try:
        await bot.close_forum_topic(
            chat_id=SUPPORT_GROUP_ID,
            message_thread_id=ticket["topic_id"],
        )
    except Exception as e:
        print(f"[WARN] Could not close forum topic {ticket['topic_id']}: {e}")

    await callback.answer(f"✅ Тикет #{ticket_id} закрыт.", show_alert=False)
    print(f"[TICKET] Ticket #{ticket_id} resolved by {callback.from_user.id} ({callback.from_user.username})")


@router.callback_query(F.data.startswith("wait_ticket_"))
async def handle_wait_ticket(callback: CallbackQuery, bot: Bot):
    """Support marks ticket as waiting for user response."""
    ticket_id = int(callback.data.split("_")[2])
    ticket = await db.get_ticket_by_id(ticket_id)

    if not ticket:
        await callback.answer("Тикет не найден.", show_alert=True)
        return

    if ticket["status"] in ("resolved", "closed_auto"):
        await callback.answer("Тикет уже закрыт.", show_alert=True)
        return

    await db.set_ticket_status(ticket_id, "waiting_user")
    await callback.answer("⏸ Статус: ожидание ответа пользователя.", show_alert=False)
    print(f"[TICKET] Ticket #{ticket_id} set to waiting_user by {callback.from_user.id}")


def _closed_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    """Disabled buttons shown after ticket is closed."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔒 Закрыт", callback_data=f"closed_{ticket_id}"),
            ]
        ]
    )


@router.callback_query(F.data.startswith("closed_"))
async def handle_closed_noop(callback: CallbackQuery):
    await callback.answer("Тикет уже закрыт.", show_alert=False)


# ── Ban callback ──────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("ban_ticket_"))
async def handle_ban_ticket(callback: CallbackQuery, bot: Bot):
    """Ban the ticket's user, close the ticket."""
    ticket_id = int(callback.data.split("_")[2])
    ticket = await db.get_ticket_by_id(ticket_id)

    if not ticket:
        await callback.answer("Тикет не найден.", show_alert=True)
        return

    user_id = ticket["telegram_id"]
    banned_by = callback.from_user.id

    # Add to blacklist
    await db.add_to_blacklist(
        telegram_id=user_id,
        reason=f"Banned via ticket #{ticket_id}",
        banned_by=banned_by,
    )

    # Close ticket if still open
    if ticket["status"] not in ("resolved", "closed_auto"):
        await db.set_ticket_status(ticket_id, "resolved")

    # Update buttons
    try:
        await callback.message.edit_reply_markup(
            reply_markup=_closed_keyboard(ticket_id)
        )
    except Exception as e:
        print(f"[WARN] Could not edit info card buttons: {e}")

    # Close forum topic
    try:
        await bot.close_forum_topic(
            chat_id=SUPPORT_GROUP_ID,
            message_thread_id=ticket["topic_id"],
        )
    except Exception as e:
        print(f"[WARN] Could not close forum topic {ticket['topic_id']}: {e}")

    await callback.answer(
        f"🚫 Пользователь {user_id} заблокирован, тикет #{ticket_id} закрыт.",
        show_alert=True,
    )
    print(f"[BAN] User {user_id} banned via ticket #{ticket_id} by {banned_by}")


# ── /unban command ────────────────────────────────────────────────────────────

@router.message(
    Command("unban"),
    F.chat.id == SUPPORT_GROUP_ID,
    F.chat.type.in_({"group", "supergroup"}),
)
async def handle_unban(message: Message):
    """Remove a user from the blacklist. Usage: /unban <telegram_id>"""
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        await message.reply("⚠️ Использование: /unban <telegram_id>")
        return

    telegram_id = int(parts[1])
    await db.remove_from_blacklist(telegram_id)
    await message.reply(f"✅ Пользователь {telegram_id} разблокирован.")
    print(f"[UNBAN] User {telegram_id} removed from blacklist by {message.from_user.id}")


# ── /blacklist command ────────────────────────────────────────────────────────

@router.message(
    Command("blacklist"),
    F.chat.id == SUPPORT_GROUP_ID,
    F.chat.type.in_({"group", "supergroup"}),
)
async def handle_blacklist(message: Message):
    """Show the current blacklist."""
    entries = await db.get_blacklist()
    if not entries:
        await message.reply("Чёрный список пуст.")
        return

    lines = ["🚫 <b>Чёрный список:</b>\n"]
    for e in entries:
        reason = e["reason"] or "—"
        banned_by = e["banned_by"] or "—"
        lines.append(
            f"• <code>{e['telegram_id']}</code> | {reason} | by {banned_by} | {e['created_at']}"
        )
    await message.reply("\n".join(lines), parse_mode="HTML")
