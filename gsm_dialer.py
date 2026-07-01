"""
GSM modem (Asterisk + chan_dongle) orqali qo'ng'iroq qilib, oldindan
saqlangan ovozli xabarni o'ynatuvchi dialer.

Ishlash usuli — Asterisk "call file" (qo'ng'iroq fayli):
har bir xodim uchun spool papkasiga kichik matn fayl tashlaymiz,
Asterisk uni ko'radi va SIZNING SIM kartangiz orqali qo'ng'iroq qiladi,
so'ng ovozli xabarni o'ynatadi.

Asterisk sozlamalari:  asterisk/dongle.conf.example va
                       asterisk/extensions.conf.example ga qarang.
"""
import os
import tempfile
import time

import config
import models


def _call_file_matni(number: str, sound_name: str) -> str:
    return (
        f"Channel: Dongle/{config.DONGLE_DEVICE}/{number}\n"
        f"CallerID: {config.CALLER_ID}\n"
        "MaxRetries: 1\n"
        "RetryTime: 60\n"
        "WaitTime: 30\n"
        f"Context: {config.BROADCAST_CONTEXT}\n"
        "Extension: s\n"
        "Priority: 1\n"
        f"Setvar: AUDIOFILE={sound_name}\n"
    )


def qongiroq_qil(number: str, sound_name: str) -> None:
    """
    Bitta raqamga qo'ng'iroq qilish uchun Asterisk call file yaratadi.
    Fayl avval vaqtinchalik joyda yoziladi, so'ng spool papkasiga
    ATOMIK ko'chiriladi (Asterisk chala faylni o'qib qolmasligi uchun).
    """
    matn = _call_file_matni(number, sound_name)
    fd, vaqtinchalik = tempfile.mkstemp(suffix=".call")
    with os.fdopen(fd, "w") as f:
        f.write(matn)

    nishon = os.path.join(
        config.ASTERISK_SPOOL_DIR, f"call_{number.strip('+')}_{int(time.time()*1000)}.call"
    )
    os.rename(vaqtinchalik, nishon)


def hammaga(sound_name: str, emp_ids: list[int] | None = None,
            kechikish: float = 1.5) -> list[dict]:
    """
    Ovozli xabarni tanlangan (yoki barcha) xodimlarga qo'ng'iroq
    qilib o'ynatadi.
    """
    royxat = models.xodimlar()
    if emp_ids:
        royxat = [x for x in royxat if int(x["id"]) in set(map(int, emp_ids))]

    natijalar = []
    for xodim in royxat:
        try:
            qongiroq_qil(xodim["telefon"], sound_name)
            natijalar.append({"xodim": xodim["ism"], "holat": "yuborildi"})
        except Exception as e:
            natijalar.append({"xodim": xodim["ism"], "xato": str(e), "holat": "xato"})
        time.sleep(kechikish)  # bir vaqtda hamma qo'ng'iroqni bosib yubormaslik uchun
    return natijalar
