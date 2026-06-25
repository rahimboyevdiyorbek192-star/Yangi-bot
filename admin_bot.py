"""
Telegram admin bot — rahbar qo'ng'iroqlarni shu yerdan boshqaradi.

Imkoniyatlar:
  /start        — panel
  /topshiriqlar — tayyor topshiriqni tanlab, qo'ng'iroqni boshlash
  /xodimlar     — xodimlar ro'yxati
  /natijalar    — oxirgi qo'ng'iroqlar natijasi

Ishga tushirish: python admin_bot.py
(app.py serveri ham ishlab turishi shart — qo'ng'iroqlar o'sha orqali boradi)
"""
import asyncio

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import caller
import config
import models
import storage

bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


def admin_mi(message: types.Message) -> bool:
    return message.from_user.id == config.ADMIN_ID


@dp.message(Command("start"))
async def start(message: types.Message):
    if not admin_mi(message):
        await message.answer("Bu bot faqat rahbar uchun.")
        return
    await message.answer(
        "\U0001F44B Qo'ng'iroq boti — admin paneli\n\n"
        "/topshiriqlar — topshiriq tanlab xodimlarga qo'ng'iroq qilish\n"
        "/xodimlar — xodimlar ro'yxati\n"
        "/natijalar — oxirgi qo'ng'iroqlar natijasi"
    )


@dp.message(Command("topshiriqlar"))
async def topshiriqlar(message: types.Message):
    if not admin_mi(message):
        return
    tugmalar = [
        [InlineKeyboardButton(text=f"\U0001F4CB {t['nomi']}", callback_data=f"task:{t['id']}")]
        for t in models.topshiriqlar()
    ]
    await message.answer(
        "Qaysi topshiriqni xodimlarga tushuntiramiz?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=tugmalar),
    )


@dp.callback_query(F.data.startswith("task:"))
async def task_tanlandi(callback: types.CallbackQuery):
    task_id = callback.data.split(":", 1)[1]
    topshiriq = models.topshiriq_top(task_id)
    if not topshiriq:
        await callback.answer("Topshiriq topilmadi", show_alert=True)
        return
    soni = len(models.xodimlar())
    tugmalar = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"\U0001F4DE Hamma {soni} xodimga qo'ng'iroq qilish",
            callback_data=f"call:{task_id}")],
    ])
    await callback.message.answer(
        f"\U0001F4CB <b>{topshiriq['nomi']}</b>\n\n{topshiriq['matn']}\n\n"
        "Qo'ng'iroqni boshlaymizmi?",
        parse_mode="HTML",
        reply_markup=tugmalar,
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("call:"))
async def qongiroq_boshla(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    task_id = callback.data.split(":", 1)[1]
    await callback.message.answer("\U0001F4DE Qo'ng'iroqlar boshlandi, biroz kuting...")
    await callback.answer()

    # Twilio sinxron ishlaydi — botni bloklamaslik uchun alohida oqimda.
    natijalar = await asyncio.to_thread(caller.hammaga, task_id)

    yuborildi = sum(1 for r in natijalar if r["holat"] == "yuborildi")
    xato = [r for r in natijalar if r["holat"] == "xato"]
    matn = f"✅ {yuborildi} ta xodimga qo'ng'iroq yuborildi."
    if xato:
        matn += "\n\n⚠️ Xatoliklar:\n" + "\n".join(
            f"• {r['xodim']}: {r['xato']}" for r in xato
        )
    matn += "\n\nNatijalarni /natijalar orqali ko'ring."
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


@dp.message(Command("natijalar"))
async def natijalar(message: types.Message):
    if not admin_mi(message):
        return
    rows = storage.natijalar(limit=20)
    if not rows:
        await message.answer("Hali natija yo'q.")
        return
    belgilar = {
        "tasdiqladi": "✅ tushundi",
        "javob_berdi": "\U0001F7E1 gaplashdi",
        "javobsiz": "\U0001F4F5 ko'tarmadi",
        "xato": "⚠️ xato",
    }
    matn = "\U0001F4CA Oxirgi qo'ng'iroqlar:\n\n"
    for r in rows:
        holat = belgilar.get(r["holat"], r["holat"])
        matn += f"• {r['emp_ism']} — {holat}\n"
    await message.answer(matn)


async def main():
    storage.init_db()
    print("✅ Admin bot ishga tushdi!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
