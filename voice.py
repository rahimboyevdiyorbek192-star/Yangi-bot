"""
O'zbekcha ovoz: matnni ovozga (TTS) va ovozni matnga (STT) aylantirish.

Asosiy provayder — Mohir AI (mohir.ai), o'zbek tili uchun eng sifatlisi.
Agar MOHIR_API_KEY kiritilmagan bo'lsa, tizim Twilio'ning o'z ovozidan
(fallback) foydalanadi — sifati pastroq, lekin ishlaydi.

ESLATMA: Mohir AI ning aniq API manzili va javob formati vaqt o'tishi
bilan o'zgarishi mumkin. Agar TTS ishlamasa, mohir.ai hujjatiga qarab
MOHIR_TTS_URL va quyidagi so'rov formatini moslang.
"""
import os
import uuid

import httpx

import config


def mohir_yoqilganmi() -> bool:
    return bool(config.MOHIR_API_KEY)


async def matndan_ovoz(matn: str) -> str | None:
    """
    Matnni o'zbekcha ovozga aylantiradi, mp3 faylga saqlaydi va
    shu faylning OMMAVIY (public) URL manzilini qaytaradi.
    Mohir sozlanmagan bo'lsa None qaytaradi (chaqiruvchi fallback ishlatadi).
    """
    if not mohir_yoqilganmi():
        return None

    fayl_nomi = f"{uuid.uuid4().hex}.mp3"
    fayl_yoli = os.path.join(config.AUDIO_DIR, fayl_nomi)

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            config.MOHIR_TTS_URL,
            headers={"Authorization": config.MOHIR_API_KEY},
            json={"text": matn, "language": "uz"},
        )
        resp.raise_for_status()
        # Mohir audio baytlarni qaytaradi deb hisoblaymiz.
        with open(fayl_yoli, "wb") as f:
            f.write(resp.content)

    return f"{config.PUBLIC_BASE_URL}/static/audio/{fayl_nomi}"


async def ovozdan_matn(audio_url: str) -> str:
    """
    Ovozli yozuvni (URL) o'zbekcha matnga aylantiradi (STT).
    Faqat Twilio <Record> ishlatadigan muqobil oqim uchun kerak.
    Standart oqimda Twilio <Gather speech> ishlatiladi va bu funksiya
    chaqirilmaydi.
    """
    if not mohir_yoqilganmi():
        return ""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            config.MOHIR_STT_URL,
            headers={"Authorization": config.MOHIR_API_KEY},
            json={"audio_url": audio_url, "language": "uz"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("text", "")
