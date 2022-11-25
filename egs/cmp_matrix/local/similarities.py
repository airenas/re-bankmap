import argparse
import math
import sys
from datetime import datetime
from enum import Enum

import numpy as np
import pandas as pd
from tqdm import tqdm

from src.utils.logger import logger
from src.utils.similarity import name_sim, date_sim, num_sim


class App:
    def __init__(self, row):
        self.type = LType.from_s(e_str(row['Type']))
        self.doc_no = e_str(row['Document_No'])
        self.entry_no = e_str(row['Entry_No'])
        self.apply_date = to_date(row['Apply_Date'])
        self.amount = e_float(row['Apply_Amount'])
        self.remaining = e_float(row['Remaining_Amount'])

    def to_str(self):
        return "{} - {} - {} ({})".format(self.type, self.apply_date, self.amount, math.isclose(self.remaining, 0))


class Entry:
    def __init__(self, row):
        self.who = e_str(row['Description'])
        self.iban = e_str(row['IBAN'])
        self.msg = e_str(row['Message'])
        self.date = datetime.fromisoformat(row['Date'])
        self.amount = e_float(row['Amount'])
        self.rec_id = e_str(row['RecAccount'])
        self.doc_id = e_str(row['RecDoc'])
        self.recognized = row['Recognized']
        self.currency = row['Currency']
        self.type = PaymentType.from_s(e_str(row['CdtDbtInd']))

    def to_str(self):
        return "{} - {} - {}".format(self.who, self.msg, self.date)


def to_date(p):
    try:
        return None if p != p else datetime.fromisoformat(p)
    except BaseException as err:
        logger.info("{}".format(p))
        raise err


class PaymentType(Enum):
    DBIT = 1
    CRDT = 2

    @staticmethod
    def from_s(s):
        if s == "CRDT":
            return PaymentType.CRDT
        if s == "DBIT":
            return PaymentType.DBIT
        raise Exception("Unknown doc type '{}'".format(s))


class DocType(Enum):
    SF = 1
    GRAZ_PAZ = 2
    GL = 3
    BA = 4

    @staticmethod
    def from_s(s):
        if s == "SF":
            return DocType.SF
        if s == "Grąž. paž.":
            return DocType.GRAZ_PAZ
        if s == "GL":
            return DocType.GL
        if s == "BA":
            return DocType.BA
        raise Exception("Unknown doc type '{}'".format(s))


class LType(Enum):
    CUST = 1
    VEND = 2
    GL = 3
    BA = 4

    @staticmethod
    def from_s(s):
        if s == "Customer":
            return LType.CUST
        if s == "Vendor":
            return LType.VEND
        if s == "GL":
            return LType.GL
        if s == "BA":
            return LType.BA
        raise Exception("Unknown type {}".format(s))


class LEntry:
    def __init__(self, row):
        try:
            self.type = LType.from_s(e_str(row['Type']))
            self.id = e_str(row['No'])
            self.name = e_str(row['Name'])
            self.iban = e_str(row['IBAN'])
            self.ext_doc = e_str(row['ExtDoc'])
            self.doc_no = e_str(row['Document_No'])
            self.due_date = to_date(row['Due_Date'])
            self.doc_date = to_date(row['Document_Date'])
            self.amount = e_float(row['Amount'])
            self.currency = row['Currency']
            self.doc_type = DocType.from_s(e_str(row['Document_Type']))
        except BaseException as err:
            raise Exception("Err: {}: for {}".format(err, row))

    def to_str(self):
        return "{} - {} - {}, {}, {}, {}, {}".format(self.type, self.id, self.name, self.doc_date, self.ext_doc,
                                                     self.doc_type, self.amount)


def e_str(p):
    if p != p:
        return ''
    return str(p).strip()


def e_float(p):
    if p != p:
        return 0
    return float(e_str(p).replace(",", "."))


def e_currency(p):
    if p != p:
        return "EUR"
    return e_str(p).upper()


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


def payment_match(ledger, entry):
    if entry.type == PaymentType.CRDT and ledger.type == LType.CUST and ledger.doc_type == DocType.SF:
        return True
    if entry.type == PaymentType.DBIT and ledger.type == LType.VEND and ledger.doc_type == DocType.SF:
        return True
    if entry.type == PaymentType.DBIT and ledger.type == LType.CUST and ledger.doc_type == DocType.GRAZ_PAZ:
        return True
    if entry.type == PaymentType.CRDT and ledger.type == LType.VEND and ledger.doc_type == DocType.GRAZ_PAZ:
        return True

    if ledger.type == LType.BA or ledger.type == LType.GL:
        return True
    return False


def amount_match(ledger, entry):
    if ledger.type == LType.BA or ledger.type == LType.GL:
        return 0.5

    diff = entry.amount - ledger.amount
    if not payment_match(ledger, entry):
        diff = entry.amount + ledger.amount
    return num_sim(diff)


def similarity(ledger, entry, prev_entries):
    res = []
    nl = ledger.name
    ne = entry.who
    res.append(1 if nl.lower() == ne.lower() else 0)
    res.append(name_sim(nl, ne))
    res.append(1 if len(ledger.iban) > 5 and ledger.iban == entry.iban else 0)
    res.append(1 if len(ledger.ext_doc) > 5 and ledger.ext_doc in entry.msg else 0)
    res.append(date_sim(ledger.due_date, entry.date))
    res.append(date_sim(entry.date, ledger.doc_date))
    res.append(amount_match(ledger, entry))
    res.append(has_past_transaction(ledger.id, prev_entries, entry))
    res.append(1 if ledger.currency == entry.currency else 0)
    res.append(1 if payment_match(ledger, entry) else 0)

    return res


sim_imp = np.array([0.5, 1, 1, 2, 0.1, .4, .3, 2, 1, 1])


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
    parser.add_argument("--top", nargs='?', default=20, type=int, help="Show the top most similar items")
    args = parser.parse_args(args=argv)

    logger.info("Starting")

    entries_t = pd.read_csv(args.input, sep=',')
    logger.info("loaded cmp_matrix {} rows".format(len(entries_t)))
    # logger.info("Headers: {}".format(list(entries_t)))
    # logger.info("\n{}".format(entries_t.head(n=10)))
    entries = [Entry(entries_t.iloc[i]) for i in range(len(entries_t))]

    ledgers = pd.read_csv(args.ledgers, sep=',')
    logger.info("loaded cmp_matrix {} rows".format(len(ledgers)))
    # logger.info("Headers: {}".format(list(ledgers)))
    # logger.info("\n{}".format(ledgers.head(n=10)))
    l_entries = [LEntry(ledgers.iloc[i]) for i in range(len(ledgers))]

    row = entries[int(args.i)]
    logger.info("Testing bank entry: \n{}".format(entries_t.iloc[int(args.i)]))
    entry_dic = {}
    for e in entries:
        k = e_key(e)
        arr = entry_dic.get(k, [])
        arr.append(e)
        entry_dic[k] = arr

    res = []
    with tqdm(desc="comparing", total=len(l_entries)) as pbar:
        for i in range(len(ledgers)):
            pbar.update(1)
            res.append({"i": i, "sim": similarity(l_entries[i], row, entry_dic), "entry": l_entries[i]})
    res.sort(key=lambda x: sim_val(x["sim"]), reverse=True)
    logger.info("Res:")
    i, was = 0, set()
    for r in res:
        if i > args.top:
            break
        if r["entry"].id in was:
            continue
        i += 1
        was.add(r["entry"].id)
        logger.info(
            "\t{} ({}): {}, {} - {}".format(i, r["i"], r["entry"].to_str(), r["sim"], sim_val(r["sim"])))
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
