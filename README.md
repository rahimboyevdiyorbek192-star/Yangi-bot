# 📞 Qo'ng'iroq Boti — AI ovozli topshiriq tizimi

Rahbar har bir xodimga qo'ng'iroq qilib topshiriq tushuntirib o'tirmasligi
uchun yaratilgan tizim. **Sun'iy intellekt (Claude) xodimning telefoniga
haqiqiy qo'ng'iroq qiladi**, topshiriqni o'zbekcha ovozda tushuntiradi va
xodim savol bersa **suhbatlashib** javob beradi — xuddi banklardagidek.

## Qanday ishlaydi?

```
Rahbar (Telegram bot)
      │  topshiriqni tanlaydi → "Hammaga qo'ng'iroq"
      ▼
caller.py ──► Twilio ──► Xodimning telefoni (+998...)  📞
      │                         ▲
      ▼                         │ ovozli suhbat
app.py (server) ◄───────────────┘
   ├─ Mohir AI  → matnni o'zbekcha OVOZGA aylantiradi (xodim eshitadi)
   ├─ Twilio    → xodimning gapini MATNGA aylantiradi (uz-UZ)
   └─ Claude AI → savolga javob beradi, topshiriqni tushuntiradi
      │
      ▼
  Natijalar SQLite bazasiga yoziladi (kim tushundi, kim ko'tarmadi)
```

## Loyiha tarkibi

| Fayl | Vazifasi |
|------|----------|
| `app.py` | Server. Twilio bilan suhbat oqimini boshqaradi |
| `caller.py` | Xodimlarga qo'ng'iroqni boshlaydi |
| `admin_bot.py` | Telegram orqali rahbar boshqaruvi |
| `brain.py` | Claude AI — suhbat miyasi |
| `voice.py` | Mohir AI — o'zbekcha ovoz (TTS/STT) |
| `models.py` | Topshiriq va xodimlar ro'yxati |
| `storage.py` | Natijalarni saqlash (SQLite) |
| `data/tasks.json` | **Tayyor topshiriqlar** (shu yerdan tahrirlang) |
| `data/employees.json` | **Xodimlar ro'yxati** (44 xodimni shu yerga yozing) |

## ⚠️ Nimalar kerak (muhim!)

Bu tizim haqiqiy telefon qiladi, shuning uchun **3 ta tashqi xizmat** kerak —
ularsiz ishlamaydi:

1. **Twilio** akkaunti (telefon qo'ng'irog'i) — [console.twilio.com](https://console.twilio.com)
   - Har qo'ng'iroq uchun **pul ketadi** (+998 ga taxminan daqiqasiga $0.10–0.40).
   - 44 ta xodim × ~2 daqiqa ≈ har topshiriq uchun bir necha dollar.
2. **Anthropic (Claude)** API kaliti (suhbat) — [console.anthropic.com](https://console.anthropic.com)
3. **Mohir AI** API kaliti (o'zbekcha ovoz) — [mohir.ai](https://mohir.ai)
   - Ixtiyoriy: bo'lmasa tizim ishlaydi, lekin ovoz o'zbekcha bo'lmaydi.

Bundan tashqari, server **internetdan ochiq (public) manzilda** turishi kerak,
chunki Twilio unga ulanadi. Sinov uchun [ngrok](https://ngrok.com) ishlatsa
bo'ladi, doimiy ish uchun esa VPS/server.

## O'rnatish

```bash
pip install -r requirements.txt

# Sozlamalar faylini tayyorlang
cp .env.example .env
# .env ni ochib, barcha kalitlarni to'ldiring (Twilio, Claude, Mohir, Telegram)
```

### Xodimlarni kiritish
`data/employees.json` faylini ochib, 44 xodimingizni yozing:
```json
[
  { "id": 1, "ism": "Aziz Karimov", "telefon": "+998901112233", "lavozim": "Sotuvchi" }
]
```
> Telefon raqamlar xalqaro formatda bo'lsin: `+998...`

### Topshiriqlarni tahrirlash
`data/tasks.json` da tayyor topshiriqlar bor. O'zingiznikini qo'shing yoki
matnini o'zgartiring.

## Ishga tushirish

**1-terminal — server:**
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
# yoki: python -m uvicorn app:app --port 8000
```

**Serverni internetga chiqarish (sinov uchun):**
```bash
ngrok http 8000
# chiqgan https manzilni .env dagi PUBLIC_BASE_URL ga yozing
```

**2-terminal — admin bot:**
```bash
python admin_bot.py
```

Endi Telegramda botga `/topshiriqlar` deb yozing, topshiriqni tanlang va
"Hamma xodimga qo'ng'iroq qilish" tugmasini bosing.

**Terminaldan ham boshlash mumkin:**
```bash
python caller.py dokon_ochish        # hammaga
python caller.py dokon_ochish 1 5    # faqat 1 va 5-xodimga
```

## Holatni tekshirish
Brauzerda `http://localhost:8000/` ni oching — qaysi sozlama yetishmayotganini
ko'rsatadi.

## Muhim eslatmalar

- **Ovoz sifati:** Eng yaxshi o'zbekcha ovoz uchun Mohir AI kalitini kiriting.
  Mohir AI ning API manzili/formati o'zgargan bo'lsa, `voice.py` va `.env`
  dagi `MOHIR_TTS_URL` ni hujjatga qarab moslang.
- **Nutqni tanish (STT):** Standart oqimda Twilio'ning `uz-UZ` nutq tanish
  xizmati ishlatiladi. Aniqlik past bo'lsa, `voice.py` dagi Mohir STT ga
  o'tish mumkin.
- **Xarajat nazorati:** Avval 1-2 xodimda sinab ko'ring (`python caller.py
  <task> 1`), keyin hammaga yuboring.
- **Maxfiylik:** `.env` faylini hech kimga bermang va GitHubga yuklamang
  (`.gitignore` da himoyalangan).

## Keyingi bosqichlar (xohlasangiz)
- Veb-panel (qo'ng'iroqlarni brauzerda boshqarish)
- Belgilangan vaqtda avtomatik qo'ng'iroq (jadval)
- Ko'tarmagan xodimga qayta qo'ng'iroq
- Hisobotni Excel/Telegramga eksport qilish
