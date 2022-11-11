import argparse
import sys
from datetime import datetime
from enum import Enum

import numpy as np
import pandas as pd
from tqdm import tqdm

from src.utils.logger import logger
from src.utils.similarity import name_sim


class Entry:
    def __init__(self, row):
        self.who = e_str(row['Description'])
        self.iban = e_str(row['IBAN'])
        self.msg = e_str(row['Message'])
        self.date = datetime.fromisoformat(row['Date'])
        self.amount = e_float(row['Amount'])
        self.rec_id = e_str(row['RecAccount'])
        self.doc_id = e_str(row['RecDoc'])

    def to_str(self):
        return "{} - {} - {}".format(self.who, self.msg, self.date)


def to_date(p):
    try:
        return None if p != p else datetime.fromisoformat(p)
    except BaseException as err:
        logger.info("{}".format(p))
        raise err


class LType(Enum):
    CUST = 1
    VEND = 2
    GL = 3

    def from_s(s):
        if s == "Customer":
            return LType.CUST
        if s == "Vendor":
            return LType.VEND
        if s == "GL":
            return LType.GL
        raise Exception("Unknown type {}".format(s))


class LEntry:
    def __init__(self, row):
        self.type = LType.from_s(e_str(row['Type']))
        self.id = e_str(row['No'])
        self.name = e_str(row['Name'])
        self.iban = e_str(row['IBAN'])
        self.ext_doc = e_str(row['ExtDoc'])
        self.due_date = to_date(row['Due_Date'])
        self.doc_date = to_date(row['Document_Date'])
        self.amount = e_float(row['Amount'])

    def to_str(self):
        return "{} - {} - {}, {}".format(self.type, self.id, self.name, self.due_date, self.ext_doc)


def e_str(p):
    if p != p:
        return ''
    return str(p)


def e_float(p):
    if p != p:
        return 0
    return float(e_str(p).replace(",", "."))


def e_key(e):
    return e.who + e.iban


def has_past_transaction(e_id, prev_entries, entry):
    for pe in prev_entries.get(e_key(entry), []):
        if entry.date <= pe.date:
            return 0
        if entry.rec_id == e_id:
            # logger.info("Found prev {} {} < {}".format(e_key(entry), pe.date, entry.date))
            return 1
    return 0


def cmp_date(due_date, date):
    if date is None or due_date is None:
        return 100
    return (due_date - date).days


def similarity(ledger, entry, prev_entries):
    res = [ledger]
    nl = ledger.name
    ne = entry.who
    res.append(1 if nl.lower() == ne.lower() else 0)
    res.append(name_sim(nl, ne))
    res.append(1 if ledger.iban == entry.iban else 0)
    res.append(1 if len(ledger.ext_doc) > 5 and ledger.ext_doc in entry.msg else 0)
    res.append(cmp_date(ledger.due_date, entry.date))
    res.append(cmp_date(entry.date, ledger.doc_date))
    res.append(ledger.amount - entry.amount)
    res.append(has_past_transaction(ledger.id, prev_entries, entry))

    return res


sim_imp = np.array([0.5, 1, 1, 2, 0.0, .0, .0, 2])


def sim_val(v):
    return np.dot(np.array(v), sim_imp)


def to_str(param):
    return "{}:{} - {} - {}".format(param["Type"], param["No"], param["Name"], param["Due_Date"])


def main(argv):
    parser = argparse.ArgumentParser(description="Calculates similarity for one item",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file of bank entries")
    parser.add_argument("--ledgers", nargs='?', required=True, help="Ledgers file")
    parser.add_argument("--i", nargs='?', required=True, help="Number of entries file to check")
    args = parser.parse_args(args=argv)

    logger.info("Starting")

    entries_t = pd.read_csv(args.input, sep=',')
    logger.info("loaded cmp_matrix {} rows".format(len(entries_t)))
    logger.info("Headers: {}".format(list(entries_t)))
    logger.info("\n{}".format(entries_t.head(n=10)))
    entries = [Entry(entries_t.iloc[i]) for i in range(len(entries_t))]

    ledgers = pd.read_csv(args.ledgers, sep=',')
    logger.info("loaded cmp_matrix {} rows".format(len(ledgers)))
    logger.info("Headers: {}".format(list(ledgers)))
    logger.info("\n{}".format(ledgers.head(n=10)))
    l_entries = [LEntry(ledgers.iloc[i]) for i in range(len(ledgers))]

    row = entries[int(args.i)]
    logger.info("Testing: \n{}".format(entries_t.iloc[int(args.i)]))
    entry_dic = {}
    for e in entries:
        k = e_key(e)
        arr = entry_dic.get(k, [])
        arr.append(e)
        entry_dic[k] = arr

    res = []
    with tqdm(desc="format cmp_matrix", total=len(l_entries)) as pbar:
        for i in range(len(ledgers)):
            pbar.update(1)
            res.append(similarity(l_entries[i], row, entry_dic))
    res.sort(key=lambda x: sim_val(x[1:]), reverse=True)
    logger.info("Res:")
    for i, r in enumerate(res[:50]):
        logger.info("\t{} - {}, {}".format(i, r[0].to_str(), r[1:]))
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
