import argparse
import sys
from datetime import datetime

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
        self.amount = float(e_str(row['Amount']).replace(",", "."))
        self.rec_id = e_str(row['RecAccount'])

    def to_str(self):
        return "{} - {} - {}".format(self.who, self.msg, self.date)


class LEntry:
    def __init__(self, row):
        self.type = e_str(row['Type'])
        self.id = e_str(row['No'])
        self.name = e_str(row['Name'])
        self.iban = e_str(row['IBAN'])
        self.ext_doc = e_str(row['ExtDoc'])
        self.due_date = datetime.fromisoformat(row['Due_Date'])
        self.doc_date = datetime.fromisoformat(row['Document_Date'])
        self.amount = float(e_str(row['Amount']).replace(",", "."))

    def to_str(self):
        return "{} - {} - {}".format(self.type, self.id, self.name, self.due_date)


def e_str(p):
    if p != p:
        return ''
    return str(p)


def similarity(ledger, entry):
    res = [ledger]
    nl = ledger.name
    ne = entry.who
    res.append(1 if nl.lower() == ne.lower() else 0)
    res.append(name_sim(nl, ne))
    res.append(1 if ledger.iban == entry.iban else 0)
    res.append(1 if len(ledger.ext_doc) > 5 and ledger.ext_doc in entry.msg else 0)
    res.append((ledger.due_date - entry.date).days)
    res.append((entry.date - ledger.doc_date).days)
    res.append(ledger.amount - entry.amount)

    return res


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
    logger.info("Testing: {}".format(row.to_str()))

    res = []
    with tqdm(desc="format cmp_matrix", total=len(l_entries)) as pbar:
        for i in range(len(ledgers)):
            pbar.update(1)
            res.append(similarity(l_entries[i], row))
    res.sort(key=lambda x: sum(x[1:]), reverse=True)
    logger.info("Res:")
    for i, r in enumerate(res[:10]):
        logger.info("\t{} - {}, {}".format(i, r[0].to_str(), r[1:]))
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
