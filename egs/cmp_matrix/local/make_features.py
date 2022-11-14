import argparse
import sys
from datetime import timedelta

import pandas as pd
from tqdm import tqdm

from egs.cmp_matrix.local.similarities import similarity, Entry, LEntry, e_key, LType
from src.utils.logger import logger


def calc_features(ledgers, row, from_i, entry_dict):
    res, fr = [], from_i
    from_t = row.date - timedelta(days=60)
    for i in range(from_i, len(ledgers)):
        le = ledgers[i]
        if le.type in [LType.VEND, LType.CUST] and le.doc_date < from_t:
            fr = i + 1
            continue
        if le.type in [LType.VEND, LType.CUST] and le.doc_date > row.date:
            break
        v = similarity(le, row, entry_dict)
        v.append(1 if row.rec_id == le.id else 0)
        res.append(v)
    return res, fr


def main(argv):
    parser = argparse.ArgumentParser(description="Make similarity features",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file of bank entries")
    parser.add_argument("--ledgers", nargs='?', required=True, help="Ledger entries file")
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
    entry_dic = {}
    for e in entries:
        k = e_key(e)
        arr = entry_dic.get(k, [])
        arr.append(e)
        entry_dic[k] = arr

    i_from = 0
    with tqdm(desc="make features", total=len(entries)) as pbar:
        for i in range(len(entries)):
            pbar.update(1)
            res, i_from = calc_features(l_entries[i_from:], entries[i], i_from, entry_dic)
            for r in res:
                # numpy.savetxt(sys.stdout, r[1:], delimiter=",")
                for i, v in enumerate(r[1:]):
                    if i == 0:
                        print("{}".format(v), end="")
                    else:
                        print(", {}".format(v), end="")
                if r[-1] == 1:
                    pass
                print("")
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
