"""DM handlers — /start, FAQ, ticket creation, user messages."""

import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import db
import faq as faq_module
from i18n import t, get_lang
from config import SUPPORT_GROUP_ID
from vpn_api import get_user_info, format_user_info_card

router = Router()


# ── States ──────────────────────────────────────────────────────────────────

class TicketStates(StatesGroup):
    waiting_for_description = State()


# ── Keyboards ────────────────────────────────────────────────────────────────

def faq_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Main FAQ inline keyboard (2 columns)."""
    buttons = [
        [
            InlineKeyboardButton(text=t(lang, "btn_cant_connect"), callback_data="faq_cant_connect"),
            InlineKeyboardButton(text=t(lang, "btn_slow"), callback_data="faq_slow"),
        ],
        [
            InlineKeyboardButton(text=t(lang, "btn_key_issue"), callback_data="faq_key_issue"),
            InlineKeyboardButton(text=t(lang, "btn_which_app"), callback_data="faq_which_app"),
        ],
        [
            InlineKeyboardButton(text=t(lang, "btn_payment"), callback_data="faq_payment"),
            InlineKeyboardButton(text=t(lang, "btn_contact_support"), callback_data="contact_support"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def helped_keyboard(lang: str, category: str) -> InlineKeyboardMarkup:
    """'Did this help?' inline keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "btn_yes"), callback_data=f"faq_helped_{category}_yes"),
                InlineKeyboardButton(text=t(lang, "btn_no"), callback_data=f"faq_helped_{category}_no"),
            ]
        ]
    )


def rating_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    """1-5 star rating keyboard."""
    stars = ["1 ⭐", "2 ⭐⭐", "3 ⭐⭐⭐", "4 ⭐⭐⭐⭐", "5 ⭐⭐⭐⭐⭐"]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=s, callback_data=f"rate_{ticket_id}_{i+1}")
                for i, s in enumerate(stars)
            ]
        ]
    )


# ── /start ───────────────────────────────────────────────────────────────────

@router.message(CommandStart(), F.chat.type == "private")
async def cmd_start(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.language_code)
    await state.clear()
    await message.answer(
        t(lang, "welcome"),
        reply_markup=faq_keyboard(lang),
        parse_mode="HTML",
    )


# ── FAQ callbacks ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.in_(faq_module.FAQ_CALLBACK_MAP.keys()))
async def handle_faq_button(callback: CallbackQuery, state: FSMContext):
    lang = get_lang(callback.from_user.language_code)
    category = faq_module.FAQ_CALLBACK_MAP[callback.data]
    content = faq_module.FAQ_CONTENT.get(category, {}).get(lang, "—")

    await callback.message.edit_text(
        text=f"{content}\n\n<i>{t(lang, 'faq_helped')}</i>",
        reply_markup=helped_keyboard(lang, category),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.callback_query(F.data == "contact_support")
async def handle_contact_support(callback: CallbackQuery, state: FSMContext):
    lang = get_lang(callback.from_user.language_code)
    await _start_ticket_creation(callback.message, callback.from_user.id, lang, state)
    await callback.answer()


@router.callback_query(F.data.startswith("faq_helped_"))
async def handle_faq_helped(callback: CallbackQuery, state: FSMContext):
    lang = get_lang(callback.from_user.language_code)
    # faq_helped_{category}_{yes|no}
    parts = callback.data.split("_")
    # parts: ['faq', 'helped', category, answer]
    answer = parts[-1]          # 'yes' or 'no'
    category = "_".join(parts[2:-1])  # reconstruct category (may contain underscores)

    # Log stat
    asyncio.create_task(db.log_faq_stat(category, helped=(answer == "yes")))

    if answer == "yes":
        await callback.message.edit_text(
            t(lang, "faq_yes_response"),
            parse_mode="HTML",
        )
        await callback.answer()
    else:
        # Transition to ticket creation
        await callback.message.edit_text(
            t(lang, "ask_describe"),
            parse_mode="HTML",
        )
        await state.set_state(TicketStates.waiting_for_description)
        await state.update_data(lang=lang)
        await callback.answer()


# ── Ticket creation ───────────────────────────────────────────────────────────

async def _start_ticket_creation(message: Message, user_id: int, lang: str, state: FSMContext):
    """Ask user to describe their problem."""
    # Check if user already has an open ticket
    existing = await db.get_open_ticket_for_user(user_id)
    if existing:
        await message.answer(
            t(lang, "already_has_ticket", id=existing["id"]),
            parse_mode="HTML",
        )
        return

    await message.answer(
        t(lang, "ask_describe"),
        parse_mode="HTML",
    )
    await state.set_state(TicketStates.waiting_for_description)
    await state.update_data(lang=lang)


@router.message(TicketStates.waiting_for_description, F.chat.type == "private")
async def handle_ticket_description(message: Message, state: FSMContext, bot: Bot):
    """Receive the first ticket message and create the topic."""
    data = await state.get_data()
    lang = data.get("lang", get_lang(message.from_user.language_code))
    user = message.from_user

    # Build subject from first 30 chars of text
    raw_text = message.text or message.caption or ""
    subject = raw_text[:30].strip() or "media"

    # Create ticket in DB
    ticket_id = await db.create_ticket(
        telegram_id=user.id,
        username=user.username,
        language=lang,
        subject=subject,
    )

    # Fetch VPN user info
    vpn_info = await get_user_info(user.id)
    info_card = format_user_info_card(vpn_info, user.id, user.username)

    # Topic name: "#42 | @username | Short description"
    username_display = f"@{user.username}" if user.username else f"id{user.id}"
    topic_name = f"#{ticket_id} | {username_display} | {subject}"[:255]

    try:
        # Create forum topic
        topic = await bot.create_forum_topic(
            chat_id=SUPPORT_GROUP_ID,
            name=topic_name,
        )
        topic_id = topic.message_thread_id

        # Save topic_id to ticket
        await db.update_ticket_topic(ticket_id, topic_id)

        # Build info card message text
        full_card = (
            f"{info_card}\n\n"
            f"📋 <b>Тикет #{ticket_id}</b>\n"
            f"{'─' * 30}\n"
            f"<b>Сообщение пользователя:</b>"
        )

        # Post info card (pinned message) with control buttons
        card_msg = await bot.send_message(
            chat_id=SUPPORT_GROUP_ID,
            message_thread_id=topic_id,
            text=full_card,
            parse_mode="HTML",
            reply_markup=_ticket_control_keyboard(ticket_id),
        )

        # Try to pin the info card
        try:
            await bot.pin_chat_message(
                chat_id=SUPPORT_GROUP_ID,
                message_id=card_msg.message_id,
                disable_notification=True,
            )
        except Exception as e:
            print(f"[WARN] Could not pin message in topic {topic_id}: {e}")

        # Forward the actual user message to the topic
        await _forward_user_message_to_topic(bot, message, SUPPORT_GROUP_ID, topic_id)

        # Log message
        await db.add_message(ticket_id, "user", raw_text or "[media]", message.message_id)

        # Confirm to user
        await message.answer(
            t(lang, "ticket_created", id=ticket_id),
            parse_mode="HTML",
        )

        await state.clear()
        print(f"[TICKET] Created ticket #{ticket_id} for user {user.id} ({user.username}), topic_id={topic_id}")

    except Exception as e:
        print(f"[ERROR] Failed to create ticket for user {user.id}: {e}")
        await message.answer(t(lang, "error_generic"), parse_mode="HTML")
        await state.clear()


def _ticket_control_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    """Control buttons pinned in the support topic."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Закрыть тикет", callback_data=f"close_ticket_{ticket_id}"),
                InlineKeyboardButton(text="⏸ В ожидании", callback_data=f"wait_ticket_{ticket_id}"),
            ]
        ]
    )


async def _forward_user_message_to_topic(bot: Bot, message: Message, chat_id: int, thread_id: int):
    """Forward user's message (any type) to the support topic."""
    try:
        if message.text:
            await bot.send_message(
                chat_id=chat_id,
                message_thread_id=thread_id,
                text=f"👤 {message.text}",
                parse_mode=None,
            )
        elif message.photo:
            await bot.send_photo(
                chat_id=chat_id,
                message_thread_id=thread_id,
                photo=message.photo[-1].file_id,
                caption=f"👤 {message.caption or ''}",
            )
        elif message.video:
            await bot.send_video(
                chat_id=chat_id,
                message_thread_id=thread_id,
                video=message.video.file_id,
                caption=f"👤 {message.caption or ''}",
            )
        elif message.document:
            await bot.send_document(
                chat_id=chat_id,
                message_thread_id=thread_id,
                document=message.document.file_id,
                caption=f"👤 {message.caption or ''}",
            )
        elif message.voice:
            await bot.send_voice(
                chat_id=chat_id,
                message_thread_id=thread_id,
                voice=message.voice.file_id,
            )
        elif message.video_note:
            await bot.send_video_note(
                chat_id=chat_id,
                message_thread_id=thread_id,
                video_note=message.video_note.file_id,
            )
        elif message.audio:
            await bot.send_audio(
                chat_id=chat_id,
                message_thread_id=thread_id,
                audio=message.audio.file_id,
                caption=f"👤 {message.caption or ''}",
            )
        elif message.sticker:
            # Stickers not supported — just note it
            await bot.send_message(
                chat_id=chat_id,
                message_thread_id=thread_id,
                text="👤 [отправил стикер]",
            )
        else:
            await bot.send_message(
                chat_id=chat_id,
                message_thread_id=thread_id,
                text="👤 [неподдерживаемый тип сообщения]",
            )
    except Exception as e:
        print(f"[ERROR] Failed to forward user message to topic {thread_id}: {e}")


# ── User messages after ticket created ───────────────────────────────────────

@router.message(F.chat.type == "private", ~F.sticker, F.from_user)
async def handle_user_dm(message: Message, state: FSMContext, bot: Bot):
    """Any DM message that isn't in a special state → find open ticket and forward."""
    # Skip service messages (no content)
    if not any([message.text, message.photo, message.video, message.document,
                message.voice, message.video_note, message.audio, message.caption]):
        return

    # Skip if in a state (handled by state handler above)
    current_state = await state.get_state()
    if current_state is not None:
        return

    user = message.from_user
    lang = get_lang(user.language_code)

    # Check for open ticket
    ticket = await db.get_open_ticket_for_user(user.id)
    if not ticket:
        # No open ticket → show FAQ menu
        await message.answer(
            t(lang, "no_open_ticket"),
            reply_markup=faq_keyboard(lang),
            parse_mode="HTML",
        )
        return

    # Forward to topic
    try:
        await _forward_user_message_to_topic(
            bot, message, SUPPORT_GROUP_ID, ticket["topic_id"]
        )
        raw_text = message.text or message.caption or ""
        await db.add_message(ticket["id"], "user", raw_text or "[media]", message.message_id)
        await db.update_ticket_activity(ticket["id"])
    except Exception as e:
        print(f"[ERROR] Failed to forward DM to topic: {e}")
        await message.answer(t(lang, "error_generic"), parse_mode="HTML")


@router.message(F.chat.type == "private", F.sticker)
async def handle_sticker_dm(message: Message, state: FSMContext):
    """Stickers in DM — show friendly error."""
    lang = get_lang(message.from_user.language_code)
    await message.answer(t(lang, "sticker_not_supported"), parse_mode="HTML")


# ── Rating callback ───────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("rate_"))
async def handle_rating(callback: CallbackQuery):
    """Save user rating after ticket resolved."""
    parts = callback.data.split("_")
    # rate_{ticket_id}_{stars}
    ticket_id = int(parts[1])
    stars = int(parts[2])
    lang = get_lang(callback.from_user.language_code)

    await db.set_ticket_rating(ticket_id, stars)
    await callback.message.edit_text(
        f"{t(lang, 'rating_saved')} {'⭐' * stars}",
        parse_mode="HTML",
    )
    await callback.answer()
    print(f"[RATING] Ticket #{ticket_id} rated {stars} stars by user {callback.from_user.id}")
