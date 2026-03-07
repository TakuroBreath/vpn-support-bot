"""VPN API client — fetches user subscription info."""

import aiohttp
from config import VPN_API_URL, VPN_BOT_SECRET

HEADERS = {"X-Bot-Secret": VPN_BOT_SECRET}


async def get_user_info(telegram_id: int) -> dict | None:
    """
    Fetch user info from the VPN API.
    Returns dict with keys: uuid, status, expires_at, plan_name, etc.
    Returns None if user not found or request failed.
    """
    url = f"{VPN_API_URL}/api/users/telegram/{telegram_id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
                elif resp.status == 404:
                    return None
                else:
                    text = await resp.text()
                    print(f"[VPN API] Unexpected status {resp.status} for tg_id={telegram_id}: {text}")
                    return None
    except aiohttp.ClientError as e:
        print(f"[VPN API] Connection error for tg_id={telegram_id}: {e}")
        return None
    except Exception as e:
        print(f"[VPN API] Unexpected error for tg_id={telegram_id}: {e}")
        return None


def format_user_info_card(user_data: dict | None, telegram_id: int, username: str | None) -> str:
    """Format the user info card to pin in the support topic."""
    username_str = f"@{username}" if username else f"tg://user?id={telegram_id}"
    tg_link = f'<a href="tg://user?id={telegram_id}">{username_str}</a>'

    lines = [
        "👤 <b>Информация о пользователе</b>",
        f"Telegram: {tg_link}",
        f"ID: <code>{telegram_id}</code>",
    ]

    if user_data:
        status = user_data.get("status", "—")
        plan = user_data.get("plan_name") or user_data.get("plan") or "—"
        expires = user_data.get("expires_at") or user_data.get("expiry") or "—"

        # Format expiry date nicely if it's a datetime string
        if expires and expires != "—":
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
                expires = dt.strftime("%d.%m.%Y %H:%M UTC")
            except Exception:
                pass

        status_emoji = {
            "active": "✅",
            "expired": "❌",
            "trial": "🆓",
            "inactive": "⏸",
        }.get(str(status).lower(), "❓")

        lines += [
            f"Статус: {status_emoji} {status}",
            f"Тариф: {plan}",
            f"Действует до: {expires}",
        ]
    else:
        lines.append("Подписка: ❓ Не найдена в системе")

    return "\n".join(lines)
