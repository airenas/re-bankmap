import argparse
import sys

import numpy as np
import pandas as pd
from tqdm import tqdm

from egs.cmp_matrix.local.data import PaymentType, LType, DocType, Entry, LEntry
from src.utils.logger import logger
from src.utils.similarity import name_sim, date_sim, num_sim, sf_sim


def e_key(e):
    return e.who.casefold() + e.iban.casefold()


def has_past_transaction(e_id, prev_entries, entry):
    for pe in prev_entries.get(e_key(entry), []):
        if entry.date <= pe.date:
            return 0
        if entry.rec_id == e_id:
            # logger.info("Found prev {} {} < {}".format(e_key(entry), pe.date, entry.date))
            return 1
    return 0


def payment_match(ledger: LEntry, entry: Entry):
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
    res.append(1 if nl.casefold() == ne.casefold() else 0)
    res.append(name_sim(nl, ne))
    res.append(1 if len(ledger.iban) > 5 and ledger.iban.casefold() == entry.iban.casefold() else 0)
    res.append(1 if len(ledger.ext_doc) > 5 and ledger.ext_doc.casefold() in entry.msg.casefold() else 0)
    res.append(sf_sim(ledger.ext_doc, entry.msg) if len(ledger.ext_doc) > 5 else 0)
    res.append(date_sim(ledger.due_date, entry.date))
    res.append(date_sim(entry.date, ledger.doc_date))
    res.append(amount_match(ledger, entry))
    res.append(has_past_transaction(ledger.id, prev_entries, entry))
    res.append(1 if ledger.currency.casefold() == entry.currency.casefold() else 0)
    res.append(1 if payment_match(ledger, entry) else 0)

    return res


def param_names():
    return ["name_eq", "name_sim", "iban_match",
            "ext_doc", "ext_doc_sim", "due_date", "entry_date", "amount_match", "has_past", "curr_match",
            "payment_match"]


# sim_imp = np.array([0.5, 1, 1, 2, 1, 0.1, .4, .3, 2, 1, 1])

#
sim_imp_old = np.array(
    [0.8186772936240162, 0.7759601414574985, 0.6753879910769478, 0.4994282505355246, 0.2803354664424518,
     0.04171040883215482, 0.1340896167558249, 0.1557017516787265, 0.870842041257321, 0.3213997112714011,
     0.8643907665920119])
sim_imp_old = np.array(
    [0.25607128042919725, 0.5545392622091483, 0.7599922353939803, 0.592719292426318, 0.07245583461062449,
     0.02032578022343305, 0.08793292752976331, 0.10274250393887863, 0.6743663682485446, 0.13389116467097448,
     0.7315231039082373])

sim_imp = np.array(
    [
        0.2819140025266791, 0.6606767297441343, 0.8631081348490344, 0.7778713844344313, 0.050954142742650636,
        0.05557921271902616, 0.046839292985310164, 0.17834836216885652, 0.9174387124912131, 0.24304468217448924,
        0.6207725177977753
    ])


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
