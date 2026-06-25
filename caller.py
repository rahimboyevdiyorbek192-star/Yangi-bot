"""
Qo'ng'iroqni boshlash — Twilio orqali xodimga telefon qiladi.

Terminaldan ishlatish:
    python caller.py dokon_ochish            # hamma xodimga
    python caller.py dokon_ochish 1 3        # faqat 1 va 3-xodimga
"""
import sys
import time

from twilio.rest import Client
from urllib.parse import urlencode

import config
import models

_client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)


def qongiroq_qil(xodim: dict, task_id: str) -> str:
    """Bitta xodimga qo'ng'iroq qiladi. Twilio CallSid qaytaradi."""
    savol = urlencode({"task_id": task_id, "emp_id": xodim["id"]})
    call = _client.calls.create(
        to=xodim["telefon"],
        from_=config.TWILIO_FROM_NUMBER,
        url=f"{config.PUBLIC_BASE_URL}/voice/start?{savol}",
        method="POST",
        status_callback=f"{config.PUBLIC_BASE_URL}/voice/status",
        status_callback_event=["completed", "no-answer", "busy", "failed"],
        status_callback_method="POST",
    )
    return call.sid


def hammaga(task_id: str, emp_ids: list[int] | None = None,
            kechikish: float = 2.0) -> list[dict]:
    """
    Topshiriqni tanlangan (yoki barcha) xodimlarga qo'ng'iroq qiladi.
    Qaytaradi: har bir urinish natijasi ro'yxati.
    """
    if not models.topshiriq_top(task_id):
        raise ValueError(f"Topshiriq topilmadi: {task_id}")

    royxat = models.xodimlar()
    if emp_ids:
        royxat = [x for x in royxat if int(x["id"]) in set(map(int, emp_ids))]

    natijalar = []
    for xodim in royxat:
        try:
            sid = qongiroq_qil(xodim, task_id)
            natijalar.append({"xodim": xodim["ism"], "sid": sid, "holat": "yuborildi"})
        except Exception as e:
            natijalar.append({"xodim": xodim["ism"], "xato": str(e), "holat": "xato"})
        time.sleep(kechikish)  # Twilio limitlarini bosib o'tmaslik uchun
    return natijalar


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Foydalanish: python caller.py <task_id> [emp_id ...]")
        print("\nMavjud topshiriqlar:")
        for t in models.topshiriqlar():
            print(f"  - {t['id']:16} {t['nomi']}")
        sys.exit(1)

    task = sys.argv[1]
    ids = [int(x) for x in sys.argv[2:]] if len(sys.argv) > 2 else None
    for r in hammaga(task, ids):
        print(r)
