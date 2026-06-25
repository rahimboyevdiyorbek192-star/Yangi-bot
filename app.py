"""
FastAPI server — Twilio telefon qo'ng'iroqlari bilan ishlaydigan "miya".

Oqim:
  1. caller.py xodimga qo'ng'iroq boshlaydi, Twilio /voice/start ga ulanadi.
  2. /voice/start  — robot salomlashadi va topshiriqni o'qiydi, so'ng
     xodimning gapini (ovozini) tinglaydi.
  3. /voice/respond — xodimning gapi matnga aylantirilgan holda keladi,
     Claude javob beradi; suhbat tugamasa yana tinglaydi.
  4. /voice/status — qo'ng'iroq yakuni (ko'tardi/ko'tarmadi) bazaga yoziladi.
"""
from urllib.parse import urlencode

from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from twilio.twiml.voice_response import Gather, VoiceResponse

import brain
import config
import models
import storage
import voice

app = FastAPI(title="Qo'ng'iroq Boti")
app.mount("/static", StaticFiles(directory=f"{config.BASE_DIR}/static"), name="static")


@app.on_event("startup")
def boshlanish() -> None:
    storage.init_db()


@app.get("/")
def salomatlik() -> dict:
    yetishmaydi = config.tekshir()
    return {"holat": "ishlayapti", "yetishmayotgan_sozlamalar": yetishmaydi}


def _action(yol: str, task_id: str, emp_id) -> str:
    return f"{config.PUBLIC_BASE_URL}{yol}?" + urlencode(
        {"task_id": task_id, "emp_id": emp_id}
    )


async def _gapir(vr: VoiceResponse, matn: str) -> None:
    """Matnni ovozga aylantirib TwiML ga qo'shadi (Mohir bo'lmasa fallback)."""
    audio_url = None
    try:
        audio_url = await voice.matndan_ovoz(matn)
    except Exception:
        audio_url = None
    if audio_url:
        vr.play(audio_url)
    else:
        # Fallback: Twilio o'z ovozi (o'zbekcha emas, sifati past).
        vr.say(matn)


def _tingla(vr: VoiceResponse, task_id: str, emp_id) -> None:
    """Xodimning javobini (ovozini) o'zbekcha tinglashni boshlaydi."""
    gather = Gather(
        input="speech",
        language="uz-UZ",
        speech_timeout="auto",
        action=_action("/voice/respond", task_id, emp_id),
        method="POST",
    )
    vr.append(gather)
    # Agar xodim jim qolsa — qayta so'raymiz.
    vr.redirect(_action("/voice/qayta", task_id, emp_id), method="POST")


@app.post("/voice/start")
async def voice_start(request: Request) -> Response:
    qp = request.query_params
    form = await request.form()
    task_id = qp.get("task_id", "")
    emp_id = qp.get("emp_id", "")
    call_sid = form.get("CallSid", "")

    topshiriq = models.topshiriq_top(task_id)
    xodim = models.xodim_top(emp_id) or {"id": emp_id, "ism": "", "lavozim": ""}
    vr = VoiceResponse()

    if not topshiriq:
        await _gapir(vr, "Kechirasiz, texnik nosozlik yuz berdi.")
        vr.hangup()
        return Response(str(vr), media_type="application/xml")

    storage.boshla(call_sid, xodim, task_id)

    ism = xodim.get("ism", "").split()[0] if xodim.get("ism") else ""
    salom = (
        f"Assalomu alaykum {ism}. Sizga bugungi topshiriq yuzasidan "
        f"qo'ng'iroq qildim. {topshiriq['matn']} "
        "Tushunarli bo'lsa 'tushundim' deng, savolingiz bo'lsa ayting."
    )
    storage.qosh_suhbat(call_sid, "assistant", salom)
    await _gapir(vr, salom)
    _tingla(vr, task_id, emp_id)
    return Response(str(vr), media_type="application/xml")


@app.post("/voice/qayta")
async def voice_qayta(request: Request) -> Response:
    qp = request.query_params
    task_id = qp.get("task_id", "")
    emp_id = qp.get("emp_id", "")
    vr = VoiceResponse()
    await _gapir(vr, "Eshitmadim. Iltimos qaytaring yoki 'tushundim' deng.")
    _tingla(vr, task_id, emp_id)
    return Response(str(vr), media_type="application/xml")


@app.post("/voice/respond")
async def voice_respond(request: Request) -> Response:
    qp = request.query_params
    form = await request.form()
    task_id = qp.get("task_id", "")
    emp_id = qp.get("emp_id", "")
    call_sid = form.get("CallSid", "")
    aytgani = (form.get("SpeechResult") or "").strip()

    topshiriq = models.topshiriq_top(task_id) or {"matn": ""}
    xodim = models.xodim_top(emp_id) or {"id": emp_id, "ism": "", "lavozim": ""}
    vr = VoiceResponse()

    if not aytgani:
        await _gapir(vr, "Eshitmadim. Savolingiz bo'lsa ayting yoki 'tushundim' deng.")
        _tingla(vr, task_id, emp_id)
        return Response(str(vr), media_type="application/xml")

    storage.qosh_suhbat(call_sid, "user", aytgani)
    tarix = storage.FAOL.get(call_sid, {}).get("history", [])

    try:
        natija = await brain.javob(call_sid, topshiriq, xodim, tarix)
    except Exception:
        natija = {"matn": "Tushunarli, rahmat. Ishingizga omad.", "tugatish": True}

    storage.qosh_suhbat(call_sid, "assistant", natija["matn"])
    await _gapir(vr, natija["matn"])

    if natija["tugatish"]:
        storage.tasdiqla(call_sid)
        vr.hangup()
    else:
        _tingla(vr, task_id, emp_id)
    return Response(str(vr), media_type="application/xml")


@app.post("/voice/status")
async def voice_status(request: Request) -> Response:
    form = await request.form()
    call_sid = form.get("CallSid", "")
    status = form.get("CallStatus", "")

    state = storage.FAOL.get(call_sid)
    if status in ("completed", "answered"):
        holat = "tasdiqladi" if state and state.get("confirmed") else "javob_berdi"
    elif status in ("no-answer", "busy"):
        holat = "javobsiz"
    elif status in ("failed", "canceled"):
        holat = "xato"
    else:
        holat = status

    storage.yakunla(call_sid, holat)
    return Response("", media_type="application/xml")
