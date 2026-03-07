import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8419721702:AAFARZabIdhXxyaMGcpASu6PE0PqeECEn3I")
SUPPORT_GROUP_ID = int(os.getenv("SUPPORT_GROUP_ID", "-1003783456372"))
VPN_API_URL = os.getenv("VPN_API_URL", "http://vpn-api:8080")
ADMIN_KEY = os.getenv("ADMIN_KEY", "32dd08846b2464d6c20b938557d84c6008d4aad636a8b779")
VPN_BOT_SECRET = "83cfeb1eec3c3491217799be180ba3766ff5775ebe6abf9719ec43ab0ee1aa40"
DB_PATH = os.getenv("DB_PATH", "/data/tickets.db")
AUTO_CLOSE_HOURS = int(os.getenv("AUTO_CLOSE_HOURS", "48"))
