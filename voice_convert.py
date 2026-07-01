"""
Telegram ovozli xabarini Asterisk o'ynatadigan formatga aylantirish.

Telegram ovozli xabar .oga (opus) formatida keladi. Asterisk esa
odatda 8000 Hz, mono, 16-bit WAV (yoki .sln/.gsm) ni o'ynatadi.
ffmpeg orqali aylantiramiz va Asterisk ovozlar papkasiga saqlaymiz.

ffmpeg o'rnatilishi shart:  sudo apt install ffmpeg
"""
import os
import subprocess

import config


def oga_to_asterisk(oga_yoli: str) -> str:
    """
    .oga faylni Asterisk formatidagi WAV ga aylantiradi va
    ASTERISK_SOUNDS_DIR ichiga BROADCAST_SOUND nomi bilan saqlaydi.
    Asterisk o'ynatadigan nomni (kengaytmasiz) qaytaradi.
    """
    chiqish = os.path.join(config.ASTERISK_SOUNDS_DIR, f"{config.BROADCAST_SOUND}.wav")
    os.makedirs(config.ASTERISK_SOUNDS_DIR, exist_ok=True)
    subprocess.run(
        [
            config.FFMPEG, "-y",
            "-i", oga_yoli,
            "-ar", "8000",     # 8 kHz
            "-ac", "1",        # mono
            "-acodec", "pcm_s16le",
            chiqish,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return config.BROADCAST_SOUND
