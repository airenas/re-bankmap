import argparse
import sys
from datetime import timedelta

import pandas as pd
from tqdm import tqdm

from egs.cmp_matrix.local.similarities import similarity, Entry, LEntry, sim_val, e_key, LType
from src.utils.logger import logger


def get_best_account(gl_entries, ledgers, row, from_i, entry_dict):
    bv, be, b, fr = -1, None, [], from_i

    def sim(entries):
        nonlocal bv, b, be
        for e in entries:
            # pbar.update(1)
            if e.type in [LType.VEND, LType.CUST] and e.doc_date > row.date:
                break
            v = similarity(e, row, entry_dict)
            out = sim_val(v)
            if bv < out:
                # logger.info("Found better: {} - {}".format(v[1:], out))
                bv = out
                b = v
                be = e

    sim(gl_entries)
    from_t = row.date - timedelta(days=60)
    for i in range(from_i, len(ledgers)):
        le = ledgers[i]
        if le.doc_date < from_t:
            fr = i
            continue
        break
    sim(ledgers[fr:])
    return be, fr, b


def main(argv):
    parser = argparse.ArgumentParser(description="Predicts similarities for all item",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file of bank entries")
    parser.add_argument("--ledgers", nargs='?', required=True, help="Ledgers file")
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
    l_entries.sort(key=lambda e: e.doc_date.timestamp() if e.doc_date else 1)
    gl_entries = [l for l in filter(lambda x: x.type in [LType.GL, LType.BA], l_entries)]
    doc_entries = [l for l in filter(lambda x: x.type in [LType.VEND, LType.CUST], l_entries)]

    entry_dic = {}
    for e in entries:
        k = e_key(e)
        arr = entry_dic.get(k, [])
        arr.append(e)
        entry_dic[k] = arr

    i_from = 0
    with tqdm(desc="predicting", total=len(entries)) as pbar:
        for i in range(len(entries)):
            pbar.update(1)
            best, i_from, sim = get_best_account(gl_entries, doc_entries, entries[i], i_from, entry_dic)
            print("{}\t{}".format(best.id if best is not None else "", sim))
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
