"""
Sozlamalar — barcha maxfiy kalitlar va parametrlar shu yerda
.env faylidan o'qiladi.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _get(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


# --- Twilio ---
TWILIO_ACCOUNT_SID = _get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = _get("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = _get("TWILIO_FROM_NUMBER")

# --- Server ---
PUBLIC_BASE_URL = _get("PUBLIC_BASE_URL").rstrip("/")
PORT = int(_get("PORT", "8000") or "8000")

# --- Claude AI ---
ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY")
BRAIN_MODEL = _get("BRAIN_MODEL", "claude-sonnet-4-6")

# --- Mohir AI (o'zbekcha ovoz) ---
MOHIR_API_KEY = _get("MOHIR_API_KEY")
MOHIR_TTS_URL = _get("MOHIR_TTS_URL", "https://mohir.ai/api/v1/tts")
MOHIR_STT_URL = _get("MOHIR_STT_URL", "https://mohir.ai/api/v1/stt")

# --- Telegram ---
TELEGRAM_BOT_TOKEN = _get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(_get("ADMIN_ID", "0") or "0")

# --- GSM modem / Asterisk (o'z SIM kartangiz orqali qo'ng'iroq) ---
# Sizning raqamingiz (xodimga shu raqamdan qo'ng'iroq ketadi)
CALLER_ID = _get("CALLER_ID")
# Asterisk chan_dongle dagi qurilma nomi (dongle.conf da sozlanadi)
DONGLE_DEVICE = _get("DONGLE_DEVICE", "dongle0")
# Asterisk qo'ng'iroq fayllarini kutadigan papka
ASTERISK_SPOOL_DIR = _get("ASTERISK_SPOOL_DIR", "/var/spool/asterisk/outgoing")
# Asterisk ovoz fayllari papkasi (ovozli xabar shu yerga saqlanadi)
ASTERISK_SOUNDS_DIR = _get("ASTERISK_SOUNDS_DIR", "/var/lib/asterisk/sounds")
# extensions.conf dagi kontekst nomi
BROADCAST_CONTEXT = _get("BROADCAST_CONTEXT", "broadcast")
# Ovozli xabar fayl nomi (kengaytmasiz — Asterisk shu nom bilan o'ynatadi)
BROADCAST_SOUND = _get("BROADCAST_SOUND", "xabar")
# ffmpeg dasturi (ogg -> wav aylantirish uchun)
FFMPEG = _get("FFMPEG", "ffmpeg")

# --- Yo'llar ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
AUDIO_DIR = os.path.join(BASE_DIR, "static", "audio")
DB_PATH = os.path.join(BASE_DIR, "data", "qongiroqlar.db")

os.makedirs(AUDIO_DIR, exist_ok=True)


def tekshir() -> list[str]:
    """Yetishmayotgan muhim sozlamalarni ro'yxat qilib qaytaradi."""
    kerakli = {
        "TWILIO_ACCOUNT_SID": TWILIO_ACCOUNT_SID,
        "TWILIO_AUTH_TOKEN": TWILIO_AUTH_TOKEN,
        "TWILIO_FROM_NUMBER": TWILIO_FROM_NUMBER,
        "PUBLIC_BASE_URL": PUBLIC_BASE_URL,
        "ANTHROPIC_API_KEY": ANTHROPIC_API_KEY,
    }
    return [nom for nom, qiymat in kerakli.items() if not qiymat]
