"""
Topshiriqlar va xodimlar ro'yxatini JSON fayllardan o'qish.
"""
import json
import config


def topshiriqlar() -> list[dict]:
    """data/tasks.json — tayyor topshiriqlar ro'yxati."""
    with open(f"{config.DATA_DIR}/tasks.json", encoding="utf-8") as f:
        return json.load(f)


def topshiriq_top(task_id: str) -> dict | None:
    for t in topshiriqlar():
        if t["id"] == task_id:
            return t
    return None


def xodimlar() -> list[dict]:
    """data/employees.json — xodimlar ro'yxati."""
    with open(f"{config.DATA_DIR}/employees.json", encoding="utf-8") as f:
        return json.load(f)


def xodim_top(emp_id: int) -> dict | None:
    for x in xodimlar():
        if int(x["id"]) == int(emp_id):
            return x
    return None
