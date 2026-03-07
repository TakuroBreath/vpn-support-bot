"""FAQ content — hardcoded troubleshooting texts in RU and EN."""

FAQ_CONTENT = {
    "cant_connect": {
        "ru": (
            "<b>🔌 Не подключается — попробуйте по шагам:</b>\n\n"
            "1️⃣ Перезапустите Happ — закройте полностью и откройте\n"
            "2️⃣ Удалите и добавьте ключ заново — «🔑 Мой ключ» в основном боте → скопируйте → импортируйте\n"
            "3️⃣ Обновите Happ до последней версии\n"
            "4️⃣ Проверьте интернет без VPN\n"
            "5️⃣ Перезагрузите устройство"
        ),
        "en": (
            "<b>🔌 Can't connect — try these steps:</b>\n\n"
            "1️⃣ Restart Happ — close it completely and reopen\n"
            "2️⃣ Delete and re-add your key — «🔑 My key» in the main bot → copy → import\n"
            "3️⃣ Update Happ to the latest version\n"
            "4️⃣ Check your internet without VPN\n"
            "5️⃣ Restart your device"
        ),
    },
    "slow": {
        "ru": (
            "<b>🐌 Медленно работает — попробуйте:</b>\n\n"
            "1️⃣ Проверьте скорость без VPN (speedtest.net)\n"
            "2️⃣ Переподключитесь — отключите VPN → подождите 5 сек → подключите\n"
            "3️⃣ Попробуйте другую сеть (Wi-Fi ↔ мобильные данные)\n"
            "4️⃣ Вечером (19-23ч) нагрузка выше, утром быстрее"
        ),
        "en": (
            "<b>🐌 Slow connection — try these steps:</b>\n\n"
            "1️⃣ Check your speed without VPN (speedtest.net)\n"
            "2️⃣ Reconnect — disable VPN → wait 5 sec → connect again\n"
            "3️⃣ Try a different network (Wi-Fi ↔ mobile data)\n"
            "4️⃣ Evenings (7-11 PM) have higher load, mornings are faster"
        ),
    },
    "key_issue": {
        "ru": (
            "<b>🔑 Проблема с ключом — попробуйте:</b>\n\n"
            "1️⃣ Скопируйте ключ заново из основного бота @DuckSurfVPNBot → «🔑 Мой ключ»\n"
            "2️⃣ Удалите старый сервер в Happ\n"
            "3️⃣ Нажмите + → «Добавить из буфера»\n"
            "4️⃣ Если не помогает — попробуйте ссылку с /xray на конце (умный роутинг)"
        ),
        "en": (
            "<b>🔑 Key issue — try these steps:</b>\n\n"
            "1️⃣ Copy your key again from the main bot @DuckSurfVPNBot → «🔑 My key»\n"
            "2️⃣ Delete the old server in Happ\n"
            "3️⃣ Tap + → «Add from clipboard»\n"
            "4️⃣ If it doesn't help — try the link ending with /xray (smart routing)"
        ),
    },
    "which_app": {
        "ru": (
            "Мы рекомендуем <b>Happ</b> — работает на всех платформах:\n\n"
            "🍎 iPhone/iPad: <a href='https://apps.apple.com/us/app/happ-proxy-utility/id6504287215'>App Store</a>\n"
            "🤖 Android: <a href='https://play.google.com/store/apps/details?id=com.happproxy'>Google Play</a>\n"
            "🪟 Windows: <a href='https://github.com/Happ-proxy/happ-desktop/releases/latest/download/setup-Happ.x64.exe'>Скачать</a>\n"
            "🍏 macOS: <a href='https://github.com/Happ-proxy/happ-desktop/releases/latest/download/Happ.macOS.universal.dmg'>Скачать</a>"
        ),
        "en": (
            "We recommend <b>Happ</b> — works on all platforms:\n\n"
            "🍎 iPhone/iPad: <a href='https://apps.apple.com/us/app/happ-proxy-utility/id6504287215'>App Store</a>\n"
            "🤖 Android: <a href='https://play.google.com/store/apps/details?id=com.happproxy'>Google Play</a>\n"
            "🪟 Windows: <a href='https://github.com/Happ-proxy/happ-desktop/releases/latest/download/setup-Happ.x64.exe'>Download</a>\n"
            "🍏 macOS: <a href='https://github.com/Happ-proxy/happ-desktop/releases/latest/download/Happ.macOS.universal.dmg'>Download</a>"
        ),
    },
    "payment": {
        "ru": (
            "<b>💳 Вопрос по оплате:</b>\n\n"
            "1️⃣ Оплата проходит через FreeKassa — если не получается, попробуйте другой способ оплаты\n"
            "2️⃣ После оплаты бот пришлёт уведомление в течение 1-2 минут\n"
            "3️⃣ Если оплатили, но уведомление не пришло — подождите 5 минут и проверьте «📊 Моя подписка»\n"
            "4️⃣ Если прошло больше 10 минут — напишите в поддержку с чеком/скриншотом"
        ),
        "en": (
            "<b>💳 Payment question:</b>\n\n"
            "1️⃣ Payment is processed via FreeKassa — if it fails, try a different payment method\n"
            "2️⃣ After payment, the bot will send a notification within 1-2 minutes\n"
            "3️⃣ If you paid but didn't get a notification — wait 5 minutes and check «📊 My subscription»\n"
            "4️⃣ If more than 10 minutes passed — contact support with your receipt/screenshot"
        ),
    },
}

# Mapping from callback_data to FAQ category key
FAQ_CALLBACK_MAP = {
    "faq_cant_connect": "cant_connect",
    "faq_slow": "slow",
    "faq_key_issue": "key_issue",
    "faq_which_app": "which_app",
    "faq_payment": "payment",
}
