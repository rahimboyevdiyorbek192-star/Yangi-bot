# 📞 Qo'ng'iroq Boti — AI ovozli topshiriq tizimi

Rahbar har bir xodimga qo'ng'iroq qilib topshiriq tushuntirib charchamasligi
uchun tizim. Telegram bot orqali boshqariladi, robot xodimlarga **telefon
qilib** topshiriqni ovozda yetkazadi.

Loyihada **2 xil ishlash usuli** bor. O'zingizga qulayini tanlang:

---

## 🅰️ VARIANT A — Bulutli (Twilio + AI suhbat)

Apparat (modem) **kerak emas**. Twilio bulut xizmati orqali qo'ng'iroq
qilinadi. Robot topshiriqni tushuntiradi va xodim **savol bersa AI javob
beradi** (ikki tomonlama suhbat).

- ➕ Apparat sotib olish shart emas, tez ishga tushadi
- ➕ AI bilan jonli suhbat
- ➖ Qo'ng'iroq chet el (Twilio) raqamidan boradi
- ➖ Har qo'ng'iroq uchun pul ketadi (Twilio tarifi)

Fayllar: `app.py`, `caller.py`, `brain.py`, `voice.py`, `admin_bot.py`

---

## 🅱️ VARIANT B — O'z SIM kartangiz (GSM modem + Asterisk) ⭐ SIZNING TANLOVINGIZ

Kompyuterga **GSM modem** orqali **o'z SIM kartangizni** o'rnatasiz.
Telegram botga **ovozli xabar** yuborasiz, bot uni **sizning raqamingizdan**
har bir xodimga qo'ng'iroq qilib eshittiradi.

```
Rahbar ──(ovozli xabar)──► Telegram bot (broadcast_bot.py)
                                │
                                ▼
                         Asterisk + chan_dongle
                                │
                     GSM modem (SIZNING SIM kartangiz) 📶
                                │
                                ▼
                     Xodimlar telefoni — SIZNING raqamingizdan 📞
                     (ovozli xabaringizni eshitishadi)
```

- ➕ Qo'ng'iroq **sizning o'z raqamingizdan** boradi
- ➕ Har qo'ng'iroq — oddiy tarifingiz bo'yicha (arzon)
- ➖ Apparat kerak (quyida) va bir marta sozlash kerak
- ➖ Bu variantda robot ovozli xabaringizni o'ynaydi (jonli AI suhbat emas)

Fayllar: `broadcast_bot.py`, `gsm_dialer.py`, `voice_convert.py`,
`asterisk/` (sozlama namunalari)

### ⚠️ Variant B uchun eng muhim narsa — TO'G'RI MODEM

**Oddiy internet dongle ovozli qo'ng'iroq QILA OLMAYDI** (u faqat internet
va SMS uchun). Sizga quyidagilardan biri kerak:

1. **Ovozni qo'llaydigan GSM modem** (voice-capable), masalan:
   `Huawei E1550`, `E169`, `E1750` (voice firmware bilan) yoki `SIM800C`
   moduli. Bularda qo'ng'iroq ovozi USB orqali o'tadi. Arzon (~$10–30).
2. Yoki **GSM shlyuz (GoIP)** qurilmasi — ishonchliroq, lekin qimmatroq.

Modem sotib olishdan oldin sotuvchidan **"voice/ovozli qo'ng'iroqni
qo'llaydimi va Asterisk chan_dongle bilan ishlaydimi?"** deb aniq so'rang.

### Variant B ni sozlash (Linux kompyuter/server)

```bash
# 1. Asterisk va ffmpeg o'rnatish
sudo apt update
sudo apt install asterisk ffmpeg

# 2. chan_dongle drayverini o'rnatish (GSM modem uchun)
#    https://github.com/wdoekes/asterisk-chan-dongle
#    (yoki Asterisk versiyangizga mos fork)

# 3. Modemni ulang va portlarini toping
ls -l /dev/ttyUSB*     # odatda ikkita: DATA va AUDIO porti

# 4. Sozlama namunalarini nusxalab moslang:
sudo cp asterisk/dongle.conf.example      /etc/asterisk/dongle.conf
sudo cp asterisk/extensions.conf.example  /etc/asterisk/  # ichini extensions.conf ga qo'shing
#    dongle.conf da data=/dev/ttyUSB1, audio=/dev/ttyUSB2 ni to'g'rilang

# 5. Asterisk qayta yuklash va modemni tekshirish
sudo asterisk -rx "dongle reload"
sudo asterisk -rx "dongle show devices"   # Status: Free bo'lsa — tayyor

# 6. Python kutubxonalar va sozlama
pip install -r requirements.txt
cp .env.example .env
#    .env da TELEGRAM_BOT_TOKEN, ADMIN_ID, CALLER_ID (o'z raqamingiz) ni to'ldiring

# 7. Xodimlarni kiriting: data/employees.json (44 xodim)

# 8. Botni ishga tushiring
python broadcast_bot.py
```

**Muhim (ruxsatlar):** Python yozadigan qo'ng'iroq fayllari Asterisk
o'qiy oladigan bo'lishi kerak. Odatda botni Asterisk bilan bir foydalanuvchi
ostida (yoki root) ishga tushirish yoki `ASTERISK_SPOOL_DIR` va
`ASTERISK_SOUNDS_DIR` ga yozish huquqini berish kerak.

### Variant B — ishlatish
1. Telegramda botga `/start` deb yozing.
2. **Ovozli xabar** yuboring (mikrofon tugmasi bilan yozib).
3. Chiqadigan **"Hamma xodimga qo'ng'iroq qilish"** tugmasini bosing.
4. Bot har bir xodimga sizning raqamingizdan qo'ng'iroq qilib, xabaringizni
   eshittiradi.

> 💡 Avval o'zingizni yoki 1 ta xodimni sinab ko'ring (`data/employees.json`
> da faqat 1 ta raqam qoldirib), keyin hammasini kiriting.

---

## Umumiy fayllar (ikkala variant uchun)

| Fayl | Vazifasi |
|------|----------|
| `data/employees.json` | **Xodimlar ro'yxati** (44 xodimni shu yerga yozing) |
| `data/tasks.json` | Tayyor topshiriqlar (Variant A da ishlatiladi) |
| `models.py` | Ro'yxatlarni o'qish |
| `storage.py` | Natijalarni saqlash |
| `config.py` | Sozlamalar (`.env` dan) |

### Xodimlarni kiritish — `data/employees.json`
```json
[
  { "id": 1, "ism": "Aziz Karimov", "telefon": "+998901112233", "lavozim": "Sotuvchi" }
]
```
> Raqamlar xalqaro formatda: `+998...`

---

## Qaysi variantni tanlash kerak?

| Savol | Variant A (Twilio) | Variant B (o'z SIM) |
|-------|:---:|:---:|
| Apparat kerakmi? | Yo'q | Ha (GSM modem) |
| Qo'ng'iroq qaysi raqamdan? | Chet el raqami | **Sizning raqamingiz** |
| AI bilan suhbat? | Ha | Yo'q (ovozli xabar) |
| Tez ishga tushadimi? | Ha | Sozlash kerak |

Siz **o'z raqamingizdan** qo'ng'iroq qilishni xohlaganingiz uchun —
**Variant B** aynan sizga mos. Twilio (Variant A) esa apparat sozlashni
xohlamasangiz, muqobil sifatida qoldirildi.

## Maxfiylik
`.env` faylini hech kimga bermang va GitHubga yuklamang (`.gitignore` da
himoyalangan).

## Keyingi bosqichlar (xohlasangiz)
- Ko'tarmagan xodimga avtomatik qayta qo'ng'iroq
- Kim ko'tardi / ko'tarmadi hisoboti (Asterisk AMI orqali)
- Belgilangan vaqtda avtomatik qo'ng'iroq (jadval)
- Variant B ga ham AI suhbatni qo'shish
