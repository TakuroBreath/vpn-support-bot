# DuckSurf VPN Support Bot — Knowledge Base

## Overview
Telegram support ticket bot that bridges users (DM) ↔ support staff (forum group topics).
Each ticket = one forum topic in the support group.

## Architecture

```
User DM → bot.py → handlers/user.py → creates topic in support group
Support → handlers/group.py → forwards to user DM
```

## Key Files

| File | Purpose |
|------|---------|
| `bot.py` | Entry point, polling, auto-close background task |
| `config.py` | Env vars (BOT_TOKEN, SUPPORT_GROUP_ID, VPN_API_URL, etc.) |
| `db.py` | All SQLite operations via aiosqlite |
| `i18n.py` | All user-facing strings in RU and EN; `t(lang, key, **kwargs)` |
| `faq.py` | Hardcoded FAQ content + callback map |
| `vpn_api.py` | VPN API client + user info card formatter |
| `handlers/user.py` | DM handlers: /start, FAQ, ticket creation, user messages, rating |
| `handlers/group.py` | Group handlers: support replies, close/wait buttons |

## Config Values

| Variable | Value |
|----------|-------|
| BOT_TOKEN | `8419721702:AAFARZabIdhXxyaMGcpASu6PE0PqeECEn3I` |
| SUPPORT_GROUP_ID | `-1003783456372` |
| VPN_API_URL | `http://vpn-api:8080` (internal docker network) |
| VPN_BOT_SECRET | `83cfeb1eec3c3491217799be180ba3766ff5775ebe6abf9719ec43ab0ee1aa40` |
| DB_PATH | `/data/tickets.db` |

## Ticket Lifecycle

```
open → waiting_user → resolved
                    ↘ closed_auto (48h inactivity)
```

## FAQ Categories

- `cant_connect` — connection issues
- `slow` — speed problems
- `key_issue` — VPN key problems
- `which_app` — recommended app info
- `payment` — billing issues

## Message Routing

### User DM → Group Topic
1. If user has open ticket → forward to `ticket.topic_id`
2. No open ticket + free text → show FAQ menu
3. `waiting_for_description` state → create new ticket

### Group Topic → User DM
1. Bot sees message in topic (message_thread_id set)
2. Finds ticket by topic_id
3. Forwards to `ticket.telegram_id` with "— DuckSurf Support" footer

## VPN API

```
GET /api/users/telegram/{tg_id}
Header: X-Bot-Secret: <secret>
Response: { uuid, status, expires_at, plan_name, ... }
```

Returns None if user not found (404) or API unavailable.

## Docker

```bash
# Build
sudo docker build -t maxtakuro/vpn-support-bot:latest .

# Run (after adding to compose)
# Mount: /data volume for tickets.db
# Network: same as vpn-api container
```

## Database Schema

- `tickets` — main ticket records
- `messages` — message log (user/support)
- `faq_stats` — FAQ helpfulness tracking

## Important Notes

1. Bot must have **Group Privacy = OFF** to read all topic messages
2. Forum group must have **Topics enabled**
3. Bot needs **admin rights** in the group to create/close topics and pin messages
4. `allowed_updates=["message", "callback_query", "my_chat_member"]` in polling
5. Auto-close runs every hour, closes tickets inactive for 48h

## Localization

Language detection:
- `language_code` starts with "ru" → Russian
- Anything else → English

All strings via `t(lang, key, **kwargs)` in `i18n.py`.

## Edge Cases Handled

- User sends sticker → friendly "not supported" message
- User sends media during ticket creation → forwarded correctly
- VPN API down → info card shows "not found in system"
- Forum topic close fails → logged, doesn't crash
- User rating after resolve → 1-5 stars stored in DB
