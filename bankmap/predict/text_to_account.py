from typing import List

from bankmap.data import Entry, TextToAccountMap, TextToAccount, LType, PaymentType


def map_account(m: TextToAccountMap, _type):
    res = None
    if m.type == LType.GL:
        res = m.credit_account if _type == PaymentType.CRDT else m.debit_account
    if not res:
        res = m.account
    return res


def make_cmp_txt(msg):
    if msg:
        return " " + msg.strip().casefold() + " "
    return ""


def matches_text(msg, part):
    _part = make_cmp_txt(part)
    if _part:
        return _part in make_cmp_txt(msg)
    return False


def matches_bank(bank_account, ta_bank_account):
    if ta_bank_account:
        return ta_bank_account == bank_account
    return True


def map_text_to_account(row: Entry, maps: List[TextToAccountMap]):
    for m in maps:
        if matches_bank(row.bank_account, m.bank_account) and matches_text(row.msg, m.text):
            return TextToAccount(_type=m.type, account=map_account(m, row.type))
    return None
