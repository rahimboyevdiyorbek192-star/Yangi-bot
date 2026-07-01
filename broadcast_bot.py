"""
Ovozli xabar tarqatuvchi Telegram bot (O'Z SIM KARTANGIZ orqali).

Ishlash tartibi:
  1. Rahbar botga OVOZLI XABAR yuboradi (mikrofon tugmasi bilan yozib).
  2. Bot xabarni Asterisk formatiga aylantirib saqlaydi.
  3. "Hamma xodimga qo'ng'iroq" tugmasi bosiladi.
  4. Asterisk + GSM modem har bir xodimga SIZNING raqamingizdan
     qo'ng'iroq qilib, o'sha ovozli xabarni eshittiradi.

Ishga tushirish:  python broadcast_bot.py
(Asterisk va GSM modem sozlangan bo'lishi shart — README ga qarang)
"""
import asyncio
import os

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import config
import gsm_dialer
import models
import voice_convert

bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Oxirgi tayyorlangan ovozli xabar (Asterisk ovoz nomi)
oxirgi_xabar: dict = {"sound": None}


def admin_mi(message: types.Message) -> bool:
    return message.from_user.id == config.ADMIN_ID


@dp.message(Command("start"))
async def start(message: types.Message):
    if not admin_mi(message):
        await message.answer("Bu bot faqat rahbar uchun.")
        return
    await message.answer(
        "\U0001F44B Ovozli qo'ng'iroq boti\n\n"
        "1️⃣ Menga OVOZLI XABAR yuboring (mikrofon tugmasi bilan yozing).\n"
        "2️⃣ So'ng chiqadigan tugma orqali xodimlarga qo'ng'iroq qiling.\n\n"
        "/xodimlar — xodimlar ro'yxati"
    )


@dp.message(F.voice)
async def ovozli_xabar(message: types.Message):
    """Rahbar ovozli xabar yuborganda — saqlaymiz va tugma chiqaramiz."""
    if not admin_mi(message):
        return
    await message.answer("\U0001F3A7 Ovozli xabar qabul qilindi, tayyorlanyapti...")

    # Telegramdan .oga faylni yuklab olamiz
    oga_yoli = os.path.join(config.AUDIO_DIR, "xabar.oga")
    await bot.download(message.voice, destination=oga_yoli)

    try:
        sound = await asyncio.to_thread(voice_convert.oga_to_asterisk, oga_yoli)
    except Exception as e:
        await message.answer(
            "⚠️ Xabarni aylantirishda xato (ffmpeg o'rnatilganmi?):\n"
            f"{e}"
        )
        return

    oxirgi_xabar["sound"] = sound
    soni = len(models.xodimlar())
    tugma = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"\U0001F4DE Hamma {soni} xodimga qo'ng'iroq qilish",
            callback_data="broadcast")],
    ])
    await message.answer(
        "✅ Ovozli xabar tayyor. Endi qo'ng'iroqni boshlaymizmi?",
        reply_markup=tugma,
    )


@dp.callback_query(F.data == "broadcast")
async def broadcast(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    sound = oxirgi_xabar.get("sound")
    if not sound:
        await callback.answer("Avval ovozli xabar yuboring", show_alert=True)
        return

    await callback.message.answer("\U0001F4DE Qo'ng'iroqlar boshlandi...")
    await callback.answer()

    natijalar = await asyncio.to_thread(gsm_dialer.hammaga, sound)
    yuborildi = sum(1 for r in natijalar if r["holat"] == "yuborildi")
    xato = [r for r in natijalar if r["holat"] == "xato"]

    matn = f"✅ {yuborildi} ta xodimga qo'ng'iroq navbatga qo'yildi."
    if xato:
        matn += "\n\n⚠️ Xatoliklar:\n" + "\n".join(
            f"• {r['xodim']}: {r['xato']}" for r in xato
        )
    await callback.message.answer(matn)


@dp.message(Command("xodimlar"))
async def xodimlar(message: types.Message):
    if not admin_mi(message):
        return
    royxat = models.xodimlar()
    matn = f"\U0001F465 Xodimlar ({len(royxat)} ta):\n\n"
    for x in royxat:
        matn += f"{x['id']}. {x['ism']} — {x.get('lavozim', '')} — {x['telefon']}\n"
    await message.answer(matn)


async def main():
    print("✅ Ovozli qo'ng'iroq boti ishga tushdi!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
