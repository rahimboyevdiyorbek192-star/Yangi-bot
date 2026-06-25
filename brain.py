"""
Suhbat miyasi — Claude AI.

Robot xodimga topshiriqni tushuntiradi va xodim savol bersa javob beradi.
Xodim "tushundim" deganda yoki savoli qolmaganda suhbatni yakunlaydi.

Javobni kafolatli formatda olish uchun "tool use" (vosita) ishlatiladi:
Claude har doim {matn, tugatish} ko'rinishida javob qaytaradi.
"""
from anthropic import AsyncAnthropic

import config

_client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

JAVOB_VOSITASI = [
    {
        "name": "javob_ber",
        "description": "Xodimga aytiladigan o'zbekcha javobni va suhbatni "
        "tugatish kerakmi yo'qligini qaytaradi.",
        "input_schema": {
            "type": "object",
            "properties": {
                "matn": {
                    "type": "string",
                    "description": "Xodimga ovoz orqali aytiladigan qisqa, "
                    "tabiiy o'zbekcha matn (1-3 gap).",
                },
                "tugatish": {
                    "type": "boolean",
                    "description": "Xodim topshiriqni tushunganini tasdiqlasa "
                    "yoki boshqa savoli qolmasa true, aks holda false.",
                },
            },
            "required": ["matn", "tugatish"],
        },
    }
]


def _tizim_prompti(topshiriq: dict, xodim: dict) -> str:
    return (
        "Sen korxona rahbarining ovozli yordamchisisan. Telefon orqali "
        f"xodim bilan gaplashyapsan. Xodim ismi: {xodim.get('ism', '')}, "
        f"lavozimi: {xodim.get('lavozim', '')}.\n\n"
        "Vazifang — quyidagi topshiriqni unga tushuntirish va savollariga "
        "javob berish:\n"
        f"«{topshiriq['matn']}»\n\n"
        "Qoidalar:\n"
        "- Faqat sof o'zbek tilida, qisqa va sodda gapir (telefon suhbati).\n"
        "- Har javobing 1-3 gapdan oshmasin.\n"
        "- Xodim savol bersa, topshiriq doirasida aniq javob ber.\n"
        "- Mavzudan chetga chiqsa, hurmat bilan topshiriqqa qaytar.\n"
        "- Xodim 'tushundim', 'xo'p', 'bo'ldi' desa yoki savoli qolmasa, "
        "qisqa rahmat ayt va tugatish=true qil.\n"
        "- Hech qachon o'zingni sun'iy intellekt ekanligingni alohida "
        "ta'kidlama, oddiy yordamchidek gapir."
    )


async def javob(call_sid: str, topshiriq: dict, xodim: dict,
                tarix: list[dict]) -> dict:
    """
    tarix — [{"role": "user"/"assistant", "content": "..."}]
    Qaytaradi: {"matn": str, "tugatish": bool}
    """
    msg = await _client.messages.create(
        model=config.BRAIN_MODEL,
        max_tokens=300,
        system=_tizim_prompti(topshiriq, xodim),
        tools=JAVOB_VOSITASI,
        tool_choice={"type": "tool", "name": "javob_ber"},
        messages=tarix or [{"role": "user", "content": "(suhbat boshlandi)"}],
    )
    for block in msg.content:
        if block.type == "tool_use" and block.name == "javob_ber":
            return {
                "matn": block.input.get("matn", ""),
                "tugatish": bool(block.input.get("tugatish", False)),
            }
    # Kutilmagan holat — xavfsiz yakun
    return {"matn": "Tushunarli, rahmat. Ishingizga omad.", "tugatish": True}
