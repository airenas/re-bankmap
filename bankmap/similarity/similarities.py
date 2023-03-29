import argparse
import sys
from typing import List

import numpy as np
import pandas as pd
from tqdm import tqdm

from bankmap.data import PaymentType, LEntry, Entry, LType, DocType, Ctx
from bankmap.logger import logger
from bankmap.similarity.similarity import num_sim, date_sim, name_sim, sf_sim


def e_key(e):
    return e.who.casefold() + e.iban.casefold()


def prepare_history_map(entries: List[Entry]):
    res = {}
    for e in entries:
        res.setdefault(e_key(e), {}).setdefault(e.rec_id, []).append(e)
    return res


def has_past_transaction(ctx: Ctx, e_id, prev_entries, entry):
    if entry.rec_id != e_id:
        return 0
    max_hist_date = entry.date - ctx.history if ctx.history else None

    for pe in prev_entries.get(e_key(entry), {}).get(e_id, []):
        if max_hist_date and pe.date < max_hist_date:
            continue
        if entry.date <= pe.date:
            return 0
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


def cached_name_sim(ctx, nl, ne):
    res_d = ctx.name_sim_cache.setdefault(nl, {})
    res = res_d.setdefault(ne, None)
    if not res:
        res = name_sim(nl, ne)
        res_d[ne] = res
    # else:
    #     logger.info("found {} {} {}".format(nl, ne, res))
    return res


def similarity(ctx: Ctx, ledger, entry, prev_entries):
    res = []
    nl = ledger.name
    ne = entry.who
    res.append(1 if nl.casefold() == ne.casefold() else 0)
    res.append(cached_name_sim(ctx, nl, ne))
    res.append(1 if len(ledger.iban) > 5 and ledger.iban.casefold() == entry.iban.casefold() else 0)
    res.append(1 if len(ledger.ext_doc) > 5 and ledger.ext_doc.casefold() in entry.msg.casefold() else 0)
    res.append(sf_sim(ledger.ext_doc, entry.msg) if len(ledger.ext_doc) > 5 else 0)
    res.append(date_sim(ledger.due_date, entry.date))
    res.append(date_sim(entry.date, ledger.doc_date))
    res.append(amount_match(ledger, entry))
    res.append(has_past_transaction(ctx, ledger.id, prev_entries, entry))
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
sim_imp_S = np.array(
    [
        0.2819140025266791, 0.6606767297441343, 0.8631081348490344, 0.7778713844344313, 0.050954142742650636,
        0.05557921271902616, 0.046839292985310164, 0.17834836216885652, 0.9174387124912131, 0.24304468217448924,
        0.6207725177977753
    ])
sim_imp_H = np.array(
    [
        0.3449750597702491, 0.3151536386806773, 0.9002393928533151, 0.42182448381963883, 0.20410161825818382,
        0.004099692328662934, 0.06602886071574558, 0.059467572404456284, 0.8381943803507718, 0.22441089863777464,
        0.49163849484216277
    ])

sim_imp_H3 = np.array(
    [
        6.333702007764452e-05, 0.5348162642591313, 0.518391870752106, 0.5102844535700198, 0.09351070868593661,
        0.0006610908536512669, 0.12342285788350205, 0.10587377105491341, 0.9056746075173757, 0.2731950221020494,
        0.578392083608941
    ])

sim_imp_U2 = np.array(
    [
        0.4374178397438139, 0.8320182667619358, 0.34839284318279357, 0.2853718866008894, 0.5975536488446007,
        0.05046288909147558, 0.01777328430479688, 0.06727564053399462, 0.962981334837424, 0.10480472303982617,
        0.9245665686233056
    ])

sim_imp = sim_imp_H


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
