import argparse
import sys

import numpy as np
import pandas as pd
from tqdm import tqdm

from egs.cmp_matrix.local.data import PaymentType, LType, DocType, Entry, LEntry
from src.utils.logger import logger
from src.utils.similarity import name_sim, date_sim, num_sim, sf_sim


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
    res.append(sf_sim(ledger.ext_doc, entry.msg) if len(ledger.ext_doc) > 5 else 0)
    res.append(date_sim(ledger.due_date, entry.date))
    res.append(date_sim(entry.date, ledger.doc_date))
    res.append(amount_match(ledger, entry))
    res.append(has_past_transaction(ledger.id, prev_entries, entry))
    res.append(1 if ledger.currency == entry.currency else 0)
    res.append(1 if payment_match(ledger, entry) else 0)

    return res


sim_imp = np.array([0.5, 1, 1, 2, 1, 0.1, .4, .3, 2, 1, 1])
# sim_imp = np.array(
#     [0.2670326530041369, 0.6522307530530618, 0.9347364895419178, 0.8688850152395576, 0.019829561804123555,
#      0.11253895189811422, 0.19235562325068553, 0.9601100546445708, 0.3121823395348446, 0.44248828278554747])


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
