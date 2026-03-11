"""VPN API client — fetches user subscription info."""

import aiohttp
from config import VPN_API_URL, VPN_BOT_SECRET, ADMIN_KEY

BOT_HEADERS = {"X-Bot-Secret": VPN_BOT_SECRET}
ADMIN_HEADERS = {"X-Admin-Key": ADMIN_KEY}
# Legacy alias kept for compatibility
HEADERS = BOT_HEADERS


async def get_user_info(telegram_id: int) -> dict | None:
    """
    Fetch user info from the VPN API.
    Returns dict with keys: uuid, status, expires_at, plan_name, etc.
    Returns None if user not found or request failed.
    """
    url = f"{VPN_API_URL}/api/users/telegram/{telegram_id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=BOT_HEADERS, timeout=aiohttp.ClientTimeout(total=5)) as resp:
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


async def get_referral_stats(uuid: str) -> dict | None:
    """
    Fetch referral stats for a subscription UUID.
    Returns dict with keys: count, total_earnings, referrals.
    Returns None if not found or request failed.
    """
    url = f"{VPN_API_URL}/api/subscriptions/{uuid}/referral-stats"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=BOT_HEADERS, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 404:
                    return None
                else:
                    text = await resp.text()
                    print(f"[VPN API] Unexpected status {resp.status} for referral-stats uuid={uuid}: {text}")
                    return None
    except aiohttp.ClientError as e:
        print(f"[VPN API] Connection error for referral-stats uuid={uuid}: {e}")
        return None
    except Exception as e:
        print(f"[VPN API] Unexpected error for referral-stats uuid={uuid}: {e}")
        return None


async def extend_subscription(uuid: str, days: int) -> dict | None:
    """
    Extend a subscription by N days via admin API.
    Returns response dict or None on failure.
    """
    url = f"{VPN_API_URL}/api/admin/subscriptions/{uuid}/extend"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"days": days}, headers=ADMIN_HEADERS, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    text = await resp.text()
                    print(f"[VPN API] Unexpected status {resp.status} for extend uuid={uuid}: {text}")
                    return None
    except aiohttp.ClientError as e:
        print(f"[VPN API] Connection error for extend uuid={uuid}: {e}")
        return None
    except Exception as e:
        print(f"[VPN API] Unexpected error for extend uuid={uuid}: {e}")
        return None


async def clear_referral_balance(uuid: str) -> dict | None:
    """
    Clear referral balance for a subscription UUID via admin API.
    Returns dict with success and cleared_amount, or None on failure.
    """
    url = f"{VPN_API_URL}/api/admin/referrals/{uuid}/clear-balance"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=ADMIN_HEADERS, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    text = await resp.text()
                    print(f"[VPN API] Unexpected status {resp.status} for clear-referral-balance uuid={uuid}: {text}")
                    return None
    except aiohttp.ClientError as e:
        print(f"[VPN API] Connection error for clear-referral-balance uuid={uuid}: {e}")
        return None
    except Exception as e:
        print(f"[VPN API] Unexpected error for clear-referral-balance uuid={uuid}: {e}")
        return None


async def format_user_info_card(user_data: dict | None, telegram_id: int, username: str | None) -> str:
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

        # Fetch referral balance
        uuid = user_data.get("uuid")
        if uuid:
            ref_stats = await get_referral_stats(uuid)
            if ref_stats is not None:
                earnings = ref_stats.get("total_earnings", 0) or 0
                earnings_rub = ref_stats.get("total_earnings_rub", earnings * 75) or 0
                lines.append(f"💰 Реферальный баланс: ${earnings:.2f} ({earnings_rub:.0f}₽)")
    else:
        lines.append("Подписка: ❓ Не найдена в системе")

    return "\n".join(lines)
