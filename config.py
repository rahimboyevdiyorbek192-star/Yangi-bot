# config.py
import os
from dotenv import load_dotenv

load_dotenv()

def _require(key: str) -> str:
    val = os.getenv(key, "").strip()
    if not val:
        raise RuntimeError(f"❌ .env faylida '{key}' bo'sh yoki yo'q. To'ldiring!")
    return val

def _require_int(key: str) -> int:
    raw = _require(key)
    try:
        return int(raw)
    except ValueError:
        raise RuntimeError(f"❌ .env faylida '{key}' raqam bo'lishi kerak, lekin '{raw}' berilgan.")

API_ID         = _require_int("API_ID")
API_HASH       = _require("API_HASH")
BOT_TOKEN      = _require("BOT_TOKEN")
SUPER_ADMIN_ID = _require_int("SUPER_ADMIN_ID")

# ADMIN_IDS — vergul bilan ajratilgan: "111,222,333"
_admin_raw = os.getenv("ADMIN_IDS", "").strip()
ADMIN_LIST = []
if _admin_raw:
    for _a in _admin_raw.split(","):
        _a = _a.strip()
        if _a.isdigit():
            ADMIN_LIST.append(int(_a))

if SUPER_ADMIN_ID not in ADMIN_LIST:
    ADMIN_LIST.insert(0, SUPER_ADMIN_ID)

# ══════════════════════════════════════════════════
# IKKINCHI USERBOT (IXTIYORIY) — skanerlash 2x tez
# ══════════════════════════════════════════════════
# Agar ikkinchi Telegram hisobi bo'lsa, .env ga qo'shing:
#
#   USERBOT2_PHONE=+998901234567
#
# Agar 2-hisob uchun alohida API_ID/API_HASH bo'lsa (ixtiyoriy):
#   USERBOT2_API_ID=12345678
#   USERBOT2_API_HASH=abcdef1234567890abcdef1234567890

# ══════════════════════════════════════════════════
# HAVOLA TEKSHIRISH — Ixtiyoriy API kalitlar
# ══════════════════════════════════════════════════
# VirusTotal (bepul hisob, kuniga 500 so'rov):
#   VIRUSTOTAL_API_KEY=abc123...
#
# AbuseIPDB (bepul hisob, oyiga 1000 so'rov):
#   ABUSEIPDB_API_KEY=abc123...
#
# URLhaus — API kalit shart EMAS (bepul, ochiq)
# playwright — "pip install playwright && playwright install chromium"
#   (ixtiyoriy: brauzer ichida sahifani ochib karta/parol shakli topadi)
