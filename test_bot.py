"""
Bot funksiyalarini test qilish.
Telegram ulanishsiz ishlaydigan barcha funksiyalar sinovdan o'tkaziladi.
"""
import asyncio
import os
import sys
import traceback
import pytest

# Test natijalari
PASS = []
FAIL = []

def ok(name):
    PASS.append(name)
    print(f"  ✅  {name}")

def fail(name, reason):
    FAIL.append(name)
    print(f"  ❌  {name}: {reason}")

def section(title):
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")


# ══════════════════════════════════════════════════════
# 1. CONFIG — bo'sh .env → xato berishi kerak
# ══════════════════════════════════════════════════════
section("1. config.py — .env validation")

try:
    import config as cfg
    fail("Bo'sh .env → RuntimeError", "Xato ko'tarilmadi!")
except RuntimeError as e:
    ok(f"Bo'sh .env → to'g'ri xato: {str(e)[:60]}")
except Exception as e:
    fail("config import", str(e))


# ══════════════════════════════════════════════════════
# 2. DATABASE — SQLite funksiyalar
# ══════════════════════════════════════════════════════
section("2. database.py — SQLite operatsiyalar")

import database as db_mod
import tempfile

_orig_db = db_mod.DB_NAME
_tmp_db  = tempfile.mktemp(suffix=".db")
db_mod.DB_NAME = _tmp_db

@pytest.mark.asyncio
async def test_database():
    try:
        await db_mod.init_db()
        ok("init_db() — jadvallar yaratildi")
    except Exception as e:
        fail("init_db()", str(e)); return

    try:
        await db_mod.add_admin(12345)
        result = await db_mod.is_admin(12345, 99999)
        assert result is True
        ok("add_admin + is_admin → True")
    except Exception as e:
        fail("add_admin/is_admin", str(e))

    try:
        result = await db_mod.is_admin(99999, 11111)
        assert result is False
        ok("is_admin noto'g'ri ID → False")
    except Exception as e:
        fail("is_admin False case", str(e))

    try:
        await db_mod.remove_admin(12345)
        result = await db_mod.is_admin(12345, 99999)
        assert result is False
        ok("remove_admin → is_admin False")
    except Exception as e:
        fail("remove_admin", str(e))

    try:
        scan_id = await db_mod.create_scan_session("@test_group", "/tmp/out.xlsx", 111)
        assert isinstance(scan_id, int) and scan_id > 0
        ok(f"create_scan_session → scan_id={scan_id}")
    except Exception as e:
        fail("create_scan_session", str(e))
        scan_id = None

    if scan_id:
        try:
            await db_mod.update_scan_progress(scan_id, 50, 200)
            await db_mod.finish_scan_session(scan_id, 'done')
            ok("update_scan_progress + finish_scan_session")
        except Exception as e:
            fail("scan progress/finish", str(e))

    try:
        await db_mod.save_user_to_bank(
            111, "@test", "Ali", "Valiyev", "alival",
            "+998901234567", "1990-01-01", "Test bio",
            "https://t.me/channel1", "❌"
        )
        ok("save_user_to_bank — yangi foydalanuvchi")
    except Exception as e:
        fail("save_user_to_bank", str(e))

    try:
        await db_mod.save_user_to_bank(
            111, "@test", "Ali YANGI", "Valiyev", "alival_new",
            "+998901234567", "1990-01-01", "Yangi bio",
            "https://t.me/channel1", "❌"
        )
        log = await db_mod.get_user_change_log(111)
        assert len(log) > 0
        ok(f"save_user_to_bank — o'zgarish tarixi saqlandi ({len(log)} ta)")
    except Exception as e:
        fail("user_change_log", str(e))

    try:
        alert_id = await db_mod.add_alert(111, "payme", "@test")
        assert isinstance(alert_id, int)
        alerts = await db_mod.list_alerts(111)
        assert len(alerts) == 1
        ok(f"add_alert + list_alerts → {len(alerts)} ta alert")
    except Exception as e:
        fail("add_alert/list_alerts", str(e))
        alert_id = None

    try:
        actives = await db_mod.get_active_alerts()
        assert len(actives) >= 1
        ok(f"get_active_alerts → {len(actives)} ta")
    except Exception as e:
        fail("get_active_alerts", str(e))

    if alert_id:
        try:
            r1 = await db_mod.check_and_record_alert_hit(alert_id, 999, "@test", 111)
            r2 = await db_mod.check_and_record_alert_hit(alert_id, 999, "@test", 111)
            assert r1 is True and r2 is False
            ok("check_and_record_alert_hit — takror false")
        except Exception as e:
            fail("alert_hit deduplication", str(e))

    try:
        inv_id = await db_mod.create_investigation("Test tergoq", 111)
        assert isinstance(inv_id, int)
        ok(f"create_investigation → inv_id={inv_id}")
    except Exception as e:
        fail("create_investigation", str(e))
        inv_id = None

    if inv_id:
        try:
            tgt_id = await db_mod.add_investigation_target(inv_id, "user_id", "123456", "test")
            targets = await db_mod.get_investigation_targets(inv_id)
            assert len(targets) == 1
            ok(f"add/get_investigation_targets → {len(targets)} ta")
        except Exception as e:
            fail("investigation_targets", str(e))

asyncio.run(test_database())
db_mod.DB_NAME = _orig_db
if os.path.exists(_tmp_db):
    os.remove(_tmp_db)


# ══════════════════════════════════════════════════════
# 3. PHISHING CHECKER — URL tahlil funksiyalari
# ══════════════════════════════════════════════════════
section("3. phishing_checker.py — URL/havola tahlil")

try:
    from phishing_checker import (
        check_url_patterns, check_brand_impersonation,
        check_homograph, check_telegram_url,
        _parse_ogg_comments, _ogg_file_info,
        OGG_MAGIC, VORBIS_MAGIC, MAX_APK_SIZE_MB, MAX_OGG_SIZE_MB
    )
    ok("phishing_checker import")
except Exception as e:
    fail("phishing_checker import", str(e))

# URL pattern tekshirish
try:
    w = check_url_patterns("http://192.168.1.1/login", "192.168.1.1")
    assert any("IP" in x for x in w)
    ok("check_url_patterns — IP manzil aniqlandi")
except Exception as e:
    fail("check_url_patterns IP", str(e))

try:
    w = check_url_patterns("http://bank-login-verify-secure.xyz/account?confirm=1&password=reset", "bank-login-verify-secure.xyz")
    assert any("so'zlar" in x or "uzun" in x or "subdomen" in x or "ko'p" in x for x in w)
    ok(f"check_url_patterns — shubhali URL aniqlandi ({len(w)} ogohlantirish)")
except Exception as e:
    fail("check_url_patterns shubhali", str(e))

try:
    w = check_url_patterns("https://google.com", "google.com")
    assert len(w) == 0
    ok("check_url_patterns — normal URL → ogohlantirish yo'q")
except Exception as e:
    fail("check_url_patterns normal", str(e))

# Brend taqlidi
try:
    w = check_brand_impersonation("payme-login.xyz")
    assert len(w) > 0 and "payme" in w[0]
    ok("check_brand_impersonation — payme taqlidi aniqlandi")
except Exception as e:
    fail("check_brand_impersonation", str(e))

try:
    w = check_brand_impersonation("google-account-verify.com")
    assert len(w) > 0
    ok("check_brand_impersonation — google taqlidi aniqlandi")
except Exception as e:
    fail("check_brand_impersonation google", str(e))

try:
    w = check_brand_impersonation("payme.uz")
    assert len(w) == 0
    ok("check_brand_impersonation — rasmiy payme.uz → xavfsiz")
except Exception as e:
    fail("check_brand_impersonation rasmiy", str(e))

# Homograf hujum
try:
    # 'а' cyrillic, 'a' latin — ko'rinishi bir xil lekin turli unicode
    w = check_homograph("pаyme.uz")  # 'а' = cyrillic U+0430
    assert len(w) > 0
    ok("check_homograph — cyrillic aralash domain aniqlandi")
except Exception as e:
    fail("check_homograph", str(e))

try:
    w = check_homograph("google.com")
    assert len(w) == 0
    ok("check_homograph — oddiy domain → xavfsiz")
except Exception as e:
    fail("check_homograph normal", str(e))

# Telegram URL tekshirish
try:
    w = check_telegram_url("https://t.me/payme_official_uz")
    assert len(w) > 0
    ok("check_telegram_url — t.me da brend taqlidi aniqlandi")
except Exception as e:
    fail("check_telegram_url", str(e))

# OGG parsing — to'g'ri bounds check
try:
    # Bo'sh data
    r = _parse_ogg_comments(b"")
    assert r["vendor"] == "" and r["comments"] == []
    ok("_parse_ogg_comments — bo'sh data → crash yo'q")
except Exception as e:
    fail("_parse_ogg_comments bo'sh", str(e))

try:
    # Kesilib qolgan data (vendor_len dan keyin ma'lumot yo'q)
    broken = b'\x03vorbis' + b'\xff\xff\xff\xff'  # vendor_len=4GB
    r = _parse_ogg_comments(broken)
    assert r["vendor"] == "" and r["comments"] == []
    ok("_parse_ogg_comments — katta vendor_len → crash yo'q")
except Exception as e:
    fail("_parse_ogg_comments katta vendor_len", str(e))

try:
    # Haqiqiy vorbis comment header sintetik
    import struct
    vendor = b"Xiph.Org libVorbis I 20150105"
    payload = (b'\x03vorbis'
               + struct.pack('<I', len(vendor)) + vendor
               + struct.pack('<I', 2)           # 2 ta comment
               + struct.pack('<I', 11) + b'TITLE=Hello'
               + struct.pack('<I', 15) + b'ARTIST=TestUser')
    r = _parse_ogg_comments(payload)
    assert r["vendor"] == vendor.decode()
    assert len(r["comments"]) == 2
    ok(f"_parse_ogg_comments — to'g'ri parse: vendor='{r['vendor'][:20]}', {len(r['comments'])} comment")
except Exception as e:
    fail("_parse_ogg_comments to'g'ri parse", str(e))

try:
    # Shubhali comment (URL bor)
    import struct
    vendor = b"TestEncoder"
    suspicious = b"COMMENT=http://evil.com/steal?token=abc123"
    payload = (b'\x03vorbis'
               + struct.pack('<I', len(vendor)) + vendor
               + struct.pack('<I', 1)
               + struct.pack('<I', len(suspicious)) + suspicious)
    r = _parse_ogg_comments(payload)
    assert len(r["suspicious"]) > 0
    ok(f"_parse_ogg_comments — shubhali URL metadatada aniqlandi")
except Exception as e:
    fail("_parse_ogg_comments shubhali URL", str(e))

# APK/OGG hajm konstantalari
try:
    assert MAX_APK_SIZE_MB == 150
    assert MAX_OGG_SIZE_MB == 50
    ok(f"Hajm konstantalari: APK={MAX_APK_SIZE_MB}MB, OGG={MAX_OGG_SIZE_MB}MB")
except Exception as e:
    fail("Hajm konstantalari", str(e))


# ══════════════════════════════════════════════════════
# 4. MUSIC SCANNER — fingerprint funksiyalari
# ══════════════════════════════════════════════════════
section("4. music_scanner.py — fingerprint taqqoslash")

try:
    from music_scanner import (
        parse_fingerprint, compare_fp_arrays,
        compare_fingerprints, compare_fingerprints_sliding,
        batch_compare_against_watches, get_fingerprint,
        _HAS_NUMPY
    )
    ok(f"music_scanner import (numpy={'ha' if _HAS_NUMPY else 'yoq'})")
except Exception as e:
    fail("music_scanner import", str(e))

try:
    fp1 = "1234567890,987654321,111222333,444555666"
    fp2 = "1234567890,987654321,111222333,444555666"
    score = compare_fingerprints(fp1, fp2)
    assert score == 1.0
    ok(f"compare_fingerprints — bir xil → score={score:.2f}")
except Exception as e:
    fail("compare_fingerprints identical", str(e))

try:
    fp1 = "1234567890,987654321,111222333,444555666"
    fp2 = "9999999999,888888888,777777777,666666666"
    score = compare_fingerprints(fp1, fp2)
    # XOR algoritmida tasodifiy sonlar ~0.5 qaytaradi (bu to'g'ri)
    # Bir xil qo'shiq 1.0, turli qo'shiq 0.7 dan past bo'ladi
    assert 0.0 <= score <= 0.7
    ok(f"compare_fingerprints — turli → score={score:.2f} (threshold 0.7 dan past)")
except Exception as e:
    fail("compare_fingerprints different", str(e))

try:
    fp1 = "1234567890,987654321,111222333,444555666"
    fp2 = ""  # Bo'sh
    score = compare_fingerprints(fp1, fp2)
    assert score == 0.0
    ok("compare_fingerprints — bo'sh fp → 0.0 (crash yo'q)")
except Exception as e:
    fail("compare_fingerprints empty", str(e))

try:
    fp = "1234567890,987654321,111222333"
    arr = parse_fingerprint(fp)
    assert len(arr) == 3
    ok(f"parse_fingerprint → {len(arr)} ta element")
except Exception as e:
    fail("parse_fingerprint", str(e))

try:
    fp1 = ",".join(str(i * 123456) for i in range(200))
    fp2 = ",".join(str(i * 123456) for i in range(50, 250))  # offset 50
    score = compare_fingerprints_sliding(fp1, fp2)
    assert score > 0.7
    ok(f"compare_fingerprints_sliding — offset qo'shiq aniqladi: score={score:.2f}")
except Exception as e:
    fail("compare_fingerprints_sliding", str(e))

try:
    # batch_compare_against_watches
    watch_fps = [(1, "Test Song", parse_fingerprint("100,200,300,400,500"))]
    all_fps   = [
        ("ch1", "TestChannel", "song1.ogg", "100,200,300,400,500"),  # 100% mos
        ("ch2", "OtherChannel", "song2.ogg", "999,888,777,666,555"),  # mos emas
    ]
    results = batch_compare_against_watches(watch_fps, all_fps, threshold=0.90)
    assert len(results) == 1
    assert results[0][0] == "ch1"
    assert results[0][5] == 100.0
    ok(f"batch_compare_against_watches — 1/2 mos topdi: {results[0][5]}%")
except Exception as e:
    fail("batch_compare_against_watches", str(e))

try:
    # Mavjud bo'lmagan fayl → crash yo'q
    fp, dur = get_fingerprint("/tmp/notexist.ogg")
    assert fp is None and dur is None
    ok("get_fingerprint — yo'q fayl → (None, None) crash yo'q")
except Exception as e:
    fail("get_fingerprint yo'q fayl", str(e))

try:
    # Bo'sh fayl → crash yo'q
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
        empty_path = f.name
    fp, dur = get_fingerprint(empty_path)
    assert fp is None
    os.remove(empty_path)
    ok("get_fingerprint — bo'sh fayl → (None, None) crash yo'q")
except Exception as e:
    fail("get_fingerprint bo'sh fayl", str(e))


# ══════════════════════════════════════════════════════
# 5. MUSIC DB — asinxron funksiyalar
# ══════════════════════════════════════════════════════
section("5. music_scanner.py — DB operatsiyalar")

import music_scanner as music_mod
import tempfile

_orig_music_db = music_mod.MUSIC_DB
_tmp_music_db  = tempfile.mktemp(suffix="_music.db")
music_mod.MUSIC_DB = _tmp_music_db

@pytest.mark.asyncio
async def test_music_db():
    try:
        await music_mod.init_music_db()
        ok("init_music_db() — jadvallar yaratildi")
    except Exception as e:
        fail("init_music_db", str(e)); return

    try:
        await music_mod.save_fingerprint("ch1", "Test Kanal", "song1.ogg", "100,200,300", 180.0)
        ok("save_fingerprint — saqlandi")
    except Exception as e:
        fail("save_fingerprint", str(e))

    try:
        total_fp, total_ch = await music_mod.get_stats()
        assert total_fp == 1 and total_ch == 1
        ok(f"get_stats → {total_fp} ta fingerprint, {total_ch} ta kanal")
    except Exception as e:
        fail("music get_stats", str(e))

    try:
        await music_mod.mark_channel_scanned("ch1")
        is_scanned = await music_mod.is_channel_scanned("ch1")
        not_scanned = await music_mod.is_channel_scanned("ch999")
        assert is_scanned is True and not_scanned is False
        ok("mark_channel_scanned + is_channel_scanned")
    except Exception as e:
        fail("mark/is_channel_scanned", str(e))

    try:
        watch_id = await music_mod.add_watch_music("100,200,300", 180.0, "Kuzatiladigan musiqa", 111)
        wlist = await music_mod.get_watch_list()
        assert len(wlist) == 1
        ok(f"add_watch_music + get_watch_list → {len(wlist)} ta")
    except Exception as e:
        fail("add/get_watch_music", str(e))
        watch_id = None

    try:
        results = await music_mod.check_against_watch_list("100,200,300", threshold=0.90)
        assert len(results) == 1 and results[0]['score'] == 100.0
        ok(f"check_against_watch_list — mos topildi: {results[0]['score']}%")
    except Exception as e:
        fail("check_against_watch_list", str(e))

    try:
        results = await music_mod.check_against_watch_list("999,888,777", threshold=0.90)
        assert len(results) == 0
        ok("check_against_watch_list — mos topilmadi → []")
    except Exception as e:
        fail("check_against_watch_list no match", str(e))

    if watch_id:
        try:
            await music_mod.delete_watch_music(watch_id)
            wlist = await music_mod.get_watch_list()
            assert len(wlist) == 0
            ok("delete_watch_music → ro'yxat bo'sh")
        except Exception as e:
            fail("delete_watch_music", str(e))

asyncio.run(test_music_db())
music_mod.MUSIC_DB = _orig_music_db
if os.path.exists(_tmp_music_db):
    os.remove(_tmp_music_db)


# ══════════════════════════════════════════════════════
# 6. TG_SCRAPERS — mantiq funksiyalari
# ══════════════════════════════════════════════════════
section("6. tg_scrapers.py — mantiq funksiyalari")

try:
    # tg_scrapers telethon talab qiladi — faqat kerakli funksiyalarni import
    import importlib, types
    # Telethon stub yaratamiz
    for mod in ['telethon', 'telethon.tl', 'telethon.tl.functions',
                'telethon.tl.functions.users', 'telethon.tl.functions.contacts',
                'telethon.tl.functions.channels', 'telethon.tl.functions.messages',
                'telethon.tl.types', 'telethon.errors']:
        sys.modules.setdefault(mod, types.ModuleType(mod))
    # Kerakli class/exception stublar
    for attr in ['GetFullUserRequest', 'ImportContactsRequest', 'DeleteContactsRequest',
                 'GetFullChannelRequest', 'JoinChannelRequest', 'ImportChatInviteRequest',
                 'InputPhoneContact', 'PeerChannel',
                 'FloodWaitError', 'ChannelPrivateError', 'RpcCallFailError']:
        for mod_name in ['telethon.tl.functions.users', 'telethon.tl.functions.contacts',
                         'telethon.tl.functions.channels', 'telethon.tl.functions.messages',
                         'telethon.tl.types', 'telethon.errors']:
            m = sys.modules[mod_name]
            if not hasattr(m, attr):
                # Exception subclass uchun
                if 'Error' in attr:
                    setattr(m, attr, type(attr, (Exception,), {'seconds': 10}))
                else:
                    setattr(m, attr, type(attr, (), {}))
    import tg_scrapers as tg
    ok("tg_scrapers import")
except Exception as e:
    fail("tg_scrapers import", str(e)[:80])

# validate_target
try:
    assert tg.validate_target("@test_group") == (True, "@test_group")
    assert tg.validate_target("https://t.me/testgroup") == (True, "https://t.me/testgroup")
    assert tg.validate_target("-1001234567890") == (True, "-1001234567890")
    assert tg.validate_target("") == (False, "")
    assert tg.validate_target("x" * 513)[0] is False
    ok("validate_target — @username, link, raqam, bo'sh, juda uzun")
except Exception as e:
    fail("validate_target", str(e))

# validate_keyword
try:
    assert tg.validate_keyword("payme") == (True, "payme")
    assert tg.validate_keyword("") == (False, "")
    assert tg.validate_keyword("x" * 201)[0] is False
    ok("validate_keyword — normal, bo'sh, juda uzun")
except Exception as e:
    fail("validate_keyword", str(e))

# _excel_safe — CSV/Excel injection
try:
    assert tg._excel_safe("=SUM(A1)") == "'=SUM(A1)"
    assert tg._excel_safe("@user") == "'@user"
    assert tg._excel_safe("+998901234567") == "'+998901234567"
    assert tg._excel_safe("-1") == "'-1"
    assert tg._excel_safe("Oddiy matn") == "Oddiy matn"
    assert tg._excel_safe(None) == ""
    assert tg._excel_safe(12345) == 12345  # raqam — o'zgarmaydi
    ok("_excel_safe — =, @, +, - uchun apostrof; normal matn; None; raqam")
except Exception as e:
    fail("_excel_safe", str(e))

# SCANNING lock
try:
    assert tg._pc_link_cache == {}
    assert tg._pc_link_lock is not None
    ok("_pc_link_cache + _pc_link_lock mavjud")
except Exception as e:
    fail("_pc_link_cache lock", str(e))


# ══════════════════════════════════════════════════════
# 7. GITIGNORE — xavfsizlik
# ══════════════════════════════════════════════════════
section("7. .gitignore — maxfiy fayllar himoyasi")

try:
    with open(".gitignore") as f:
        content = f.read()
    checks = {".env": ".env" in content,
              "*.session": "*.session" in content,
              "*.db": "*.db" in content}
    for name, ok_ in checks.items():
        if ok_:
            ok(f".gitignore — '{name}' bloklangan")
        else:
            fail(".gitignore", f"'{name}' bloklangan emas")
except Exception as e:
    fail(".gitignore o'qish", str(e))


# ══════════════════════════════════════════════════════
# XULOSA
# ══════════════════════════════════════════════════════
total = len(PASS) + len(FAIL)
print(f"\n{'═'*55}")
print(f"  NATIJA: {len(PASS)}/{total} test muvaffaqiyatli")
print(f"{'═'*55}")
if FAIL:
    print(f"\n  Muvaffaqiyatsiz ({len(FAIL)} ta):")
    for f in FAIL:
        print(f"    ❌  {f}")
print()
