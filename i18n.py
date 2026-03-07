STRINGS = {
    "ru": {
        # /start
        "welcome": (
            "👋 Привет! Это служба поддержки <b>DuckSurf VPN</b> 🦆\n\n"
            "Выберите тему, чтобы получить быструю помощь, или напишите в поддержку напрямую."
        ),
        "faq_menu_title": "📋 Часто задаваемые вопросы:",

        # FAQ buttons
        "btn_cant_connect": "🔌 Не подключается",
        "btn_slow": "🐌 Медленно работает",
        "btn_key_issue": "🔑 Проблема с ключом",
        "btn_which_app": "📱 Какое приложение?",
        "btn_payment": "💳 Вопрос по оплате",
        "btn_contact_support": "💬 Написать в поддержку",

        # FAQ help prompt
        "faq_helped": "Помогло?",
        "btn_yes": "✅ Да",
        "btn_no": "❌ Нет",
        "faq_yes_response": "Рады помочь! 🦆",

        # Ticket creation
        "ask_describe": (
            "📝 Опишите вашу проблему подробнее.\n\n"
            "Можете прикрепить скриншот или видео — это поможет разобраться быстрее."
        ),
        "ticket_created": "✅ Тикет #{id} создан. Мы ответим в ближайшее время!",
        "ticket_message_forwarded": "💬 Ваше сообщение передано в поддержку.",

        # No open ticket
        "no_open_ticket": (
            "👋 Выберите тему или нажмите 💬 «Написать в поддержку»:"
        ),

        # Already has open ticket
        "already_has_ticket": (
            "📬 У вас уже открыт тикет #{id}.\n"
            "Все ваши сообщения будут переданы в поддержку автоматически."
        ),

        # Ticket resolved notification
        "ticket_resolved": (
            "✅ Ваш тикет #{id} решён!\n\n"
            "Если у вас остались вопросы — просто напишите снова."
        ),
        "rate_support": "⭐ Оцените качество поддержки:",
        "btn_star_1": "1 ⭐",
        "btn_star_2": "2 ⭐⭐",
        "btn_star_3": "3 ⭐⭐⭐",
        "btn_star_4": "4 ⭐⭐⭐⭐",
        "btn_star_5": "5 ⭐⭐⭐⭐⭐",
        "rating_saved": "Спасибо за оценку! 🦆",

        # Auto-close
        "auto_closed": (
            "🔒 Ваш тикет #{id} был автоматически закрыт после 48 часов неактивности.\n\n"
            "Если проблема не решена — напишите снова, и мы создадим новый тикет."
        ),

        # Support footer
        "support_footer": "\n\n— DuckSurf Support",

        # Errors
        "error_generic": "⚠️ Произошла ошибка. Попробуйте позже или напишите /start.",
        "sticker_not_supported": "😅 Стикеры не поддерживаются. Опишите проблему текстом или прикрепите файл/фото.",
    },
    "en": {
        # /start
        "welcome": (
            "👋 Hello! This is <b>DuckSurf VPN</b> support 🦆\n\n"
            "Choose a topic to get quick help, or contact support directly."
        ),
        "faq_menu_title": "📋 Frequently asked questions:",

        # FAQ buttons
        "btn_cant_connect": "🔌 Can't connect",
        "btn_slow": "🐌 Slow connection",
        "btn_key_issue": "🔑 Key issue",
        "btn_which_app": "📱 Which app?",
        "btn_payment": "💳 Payment question",
        "btn_contact_support": "💬 Contact support",

        # FAQ help prompt
        "faq_helped": "Did this help?",
        "btn_yes": "✅ Yes",
        "btn_no": "❌ No",
        "faq_yes_response": "Glad to help! 🦆",

        # Ticket creation
        "ask_describe": (
            "📝 Please describe your issue in detail.\n\n"
            "You can attach a screenshot or video — it helps us resolve things faster."
        ),
        "ticket_created": "✅ Ticket #{id} created. We'll respond shortly!",
        "ticket_message_forwarded": "💬 Your message has been sent to support.",

        # No open ticket
        "no_open_ticket": (
            "👋 Choose a topic or tap 💬 «Contact support»:"
        ),

        # Already has open ticket
        "already_has_ticket": (
            "📬 You already have an open ticket #{id}.\n"
            "All your messages will be forwarded to support automatically."
        ),

        # Ticket resolved notification
        "ticket_resolved": (
            "✅ Your ticket #{id} has been resolved!\n\n"
            "If you have more questions — just write again."
        ),
        "rate_support": "⭐ Rate the support quality:",
        "btn_star_1": "1 ⭐",
        "btn_star_2": "2 ⭐⭐",
        "btn_star_3": "3 ⭐⭐⭐",
        "btn_star_4": "4 ⭐⭐⭐⭐",
        "btn_star_5": "5 ⭐⭐⭐⭐⭐",
        "rating_saved": "Thanks for your feedback! 🦆",

        # Auto-close
        "auto_closed": (
            "🔒 Your ticket #{id} was automatically closed after 48 hours of inactivity.\n\n"
            "If the issue is not resolved — write again and we'll create a new ticket."
        ),

        # Support footer
        "support_footer": "\n\n— DuckSurf Support",

        # Errors
        "error_generic": "⚠️ An error occurred. Please try again later or send /start.",
        "sticker_not_supported": "😅 Stickers are not supported. Please describe the issue in text or attach a file/photo.",
    },
}


def get_lang(language_code: str | None) -> str:
    """Detect language: 'ru' if starts with 'ru', otherwise 'en'."""
    if language_code and language_code.startswith("ru"):
        return "ru"
    return "en"


def t(lang: str, key: str, **kwargs) -> str:
    """Get a translated string for given language and key."""
    strings = STRINGS.get(lang, STRINGS["en"])
    text = strings.get(key, STRINGS["en"].get(key, f"[{key}]"))
    if kwargs:
        text = text.format(**kwargs)
    return text
