import json
from datetime import datetime


def empty_if_n(v):
    return "" if v is None else v


def str_date(v: datetime):
    if v is None:
        return ""
    return v.replace(microsecond=0).isoformat()


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


def json_str(d):
    return json.dumps(d, ensure_ascii=False, cls=DateTimeEncoder)
