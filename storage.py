"""
Qo'ng'iroqlar holatini saqlash:
  - Suhbat tarixi xotirada (RAM) — qo'ng'iroq davom etayotganda kerak.
  - Natijalar SQLite bazasida — kim ko'tardi, tasdiqladimi, nima dedi.
"""
import sqlite3
import time
from contextlib import closing

import config

# Faol qo'ng'iroqlarning suhbat holati. Kalit = Twilio CallSid
# {call_sid: {"emp_id", "task_id", "history": [...], "confirmed": bool}}
FAOL: dict[str, dict] = {}


def init_db() -> None:
    with closing(sqlite3.connect(config.DB_PATH)) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS qongiroqlar (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                call_sid    TEXT,
                emp_id      INTEGER,
                emp_ism     TEXT,
                telefon     TEXT,
                task_id     TEXT,
                holat       TEXT,        -- boshlandi/javob_berdi/tasdiqladi/javobsiz/xato
                tasdiqlandi INTEGER DEFAULT 0,
                suhbat      TEXT,        -- to'liq suhbat matni
                vaqt        REAL
            )
            """
        )
        db.commit()


def boshla(call_sid: str, emp: dict, task_id: str) -> None:
    FAOL[call_sid] = {
        "emp_id": emp["id"],
        "emp_ism": emp.get("ism", ""),
        "telefon": emp.get("telefon", ""),
        "task_id": task_id,
        "history": [],
        "confirmed": False,
    }


def qosh_suhbat(call_sid: str, rol: str, matn: str) -> None:
    if call_sid in FAOL:
        FAOL[call_sid]["history"].append({"role": rol, "content": matn})


def tasdiqla(call_sid: str) -> None:
    if call_sid in FAOL:
        FAOL[call_sid]["confirmed"] = True


def yakunla(call_sid: str, holat: str) -> None:
    """Qo'ng'iroq tugadi — natijani bazaga yozamiz va RAM dan o'chiramiz."""
    state = FAOL.pop(call_sid, None)
    if not state:
        return
    suhbat = "\n".join(
        f"{'Robot' if h['role'] == 'assistant' else 'Xodim'}: {h['content']}"
        for h in state["history"]
    )
    with closing(sqlite3.connect(config.DB_PATH)) as db:
        db.execute(
            """INSERT INTO qongiroqlar
               (call_sid, emp_id, emp_ism, telefon, task_id, holat,
                tasdiqlandi, suhbat, vaqt)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                call_sid,
                state["emp_id"],
                state["emp_ism"],
                state["telefon"],
                state["task_id"],
                holat,
                1 if state["confirmed"] else 0,
                suhbat,
                time.time(),
            ),
        )
        db.commit()


def natijalar(task_id: str | None = None, limit: int = 50) -> list[dict]:
    with closing(sqlite3.connect(config.DB_PATH)) as db:
        db.row_factory = sqlite3.Row
        if task_id:
            rows = db.execute(
                "SELECT * FROM qongiroqlar WHERE task_id=? ORDER BY id DESC LIMIT ?",
                (task_id, limit),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM qongiroqlar ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]
