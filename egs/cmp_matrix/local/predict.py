import argparse
import sys
from datetime import timedelta

import pandas as pd
from tqdm import tqdm

from egs.cmp_matrix.local.similarities import similarity, Entry, LEntry
from src.utils.logger import logger


def get_best_account(ledgers, row, from_i):
    bv, b, fr = 0, None, from_i
    from_t = row.date - timedelta(days=60)
    for i in range(from_i, len(ledgers)):
        le = ledgers[i]
        if le.doc_date < from_t:
            fr = i + 1
            continue
        if le.doc_date > row.date:
            break
        v = similarity(le, row)
        if bv < sum(v[1:]):
            bv = sum(v[1:])
            b = v[0]
    return b, fr


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
    l_entries.sort(key=lambda e: e.doc_date)

    i_from = 0
    with tqdm(desc="predicting", total=len(entries)) as pbar:
        for i in range(len(entries)):
            pbar.update(1)
            best, i_from = get_best_account(l_entries[i_from:], entries[i], i_from)
            print("{}".format(best.id if best is not None else ""))
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
