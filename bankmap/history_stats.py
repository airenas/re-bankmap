from collections import Counter
from typing import List

from bankmap.data import Entry, LType


def stat_target_key(rec_type, rec_id):
    return rec_type + ":" + rec_id


class StatData:
    def __init__(self):
        self.count = 0
        self.items = Counter()

    def add(self, entry: Entry):
        if entry.rec_type == LType.UNSET:
            return
        key = stat_target_key(entry.rec_type.to_s(), entry.rec_id)
        if key:
            self.count += 1
        self.items[key] += 1

    def prob(self, target_key):
        if self.count < 1:
            return 0
        return self.items.get(target_key, 0) / self.count


def who_stat_key(e: Entry):
    return e.who + ":" + e.bank_account


def iban_stat_key(e: Entry):
    return e.iban + ":" + e.bank_account


def iban_msgc_stat_key(e: Entry):
    return e.iban + ":" + e.msg_clean + ":" + e.bank_account


def who_msgc_stat_key(e: Entry):
    return e.who + ":" + e.msg_clean + ":" + e.bank_account


class Stats:
    def __init__(self, entries: List[Entry]):
        self.who = Stat(entries=entries, key_func=who_stat_key)
        self.iban = Stat(entries=entries, key_func=iban_stat_key)
        self.iban_msgc = Stat(entries=entries, key_func=iban_msgc_stat_key)
        self.who_msgc = Stat(entries=entries, key_func=who_msgc_stat_key)

    def move(self, dt):
        self.who.move(dt)
        self.iban.move(dt)
        self.iban_msgc.move(dt)
        self.who_msgc.move(dt)


class Stat:
    def __init__(self, entries: List[Entry], key_func):
        self.entries = entries
        self.from_entry = 0
        self.key_func = key_func
        self.stats = {}

    def move(self, dt):
        while self.from_entry < len(self.entries):
            entry = self.entries[self.from_entry]
            if entry.date >= dt:
                break
            self.from_entry += 1
            stats = self.stats.setdefault(self.key_func(entry), StatData())
            stats.add(entry)

    def prob(self, entry: Entry, target_key):
        data = self.stats.get(self.key_func(entry), None)
        if data is not None:
            return data.prob(target_key)
        return 0
