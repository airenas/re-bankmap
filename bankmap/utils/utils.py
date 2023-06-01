from datetime import datetime


def empty_if_n(v):
    return "" if v is None else v


def str_date(v: datetime):
    if v is None:
        return ""
    return v.replace(microsecond=0).isoformat()
