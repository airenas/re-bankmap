import argparse
import sys

import pandas as pd
from tqdm import tqdm

from egs.cmp_matrix.local.data import App, Arena
from egs.cmp_matrix.local.similarities import Entry, LEntry
from src.utils.logger import logger


def calc(arena, row: Entry):
    docs = set([x for x in row.doc_ids.split(";") if x])
    if len(docs) == 0:
        return 0, 0
    dt = row.date
    arena.move(dt)
    found = set()
    for e in arena.playground.values():
        if e.doc_no in docs:
            found.add(e.doc_no)
    return len(docs), len(docs) - len(found)


def main(argv):
    parser = argparse.ArgumentParser(description="Predic for all item",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file of bank entries")
    parser.add_argument("--ledgers", nargs='?', required=True, help="Ledgers file")
    parser.add_argument("--apps", nargs='?', required=True, help="Applications file")
    args = parser.parse_args(args=argv)

    logger.info("Starting")

    entries_t = pd.read_csv(args.input, sep=',')
    logger.info("loaded entries {} rows".format(len(entries_t)))
    logger.info("Headers: {}".format(list(entries_t)))
    logger.info("\n{}".format(entries_t.head(n=10)))
    entries = [Entry(entries_t.iloc[i]) for i in range(len(entries_t))]

    ledgers = pd.read_csv(args.ledgers, sep=',')
    logger.info("loaded ledgers {} rows".format(len(ledgers)))
    logger.info("Headers: {}".format(list(ledgers)))
    logger.info("\n{}".format(ledgers.head(n=10)))
    l_entries = [LEntry(ledgers.iloc[i]) for i in range(len(ledgers))]

    apps_t = pd.read_csv(args.apps, sep=',')
    logger.info("loaded apps {} rows".format(len(apps_t)))
    logger.info("Headers: {}".format(list(apps_t)))
    logger.info("\n{}".format(apps_t.head(n=10)))
    apps = [App(apps_t.iloc[i]) for i in range(len(apps_t))]

    arena = Arena(l_entries, apps)

    entries.sort(key=lambda e: e.date.timestamp() if e.date else 1)

    c_all, c_missed = 0, 0
    with tqdm(desc="calc oracle", total=len(entries)) as pbar:
        for i in range(len(entries)):
            pbar.update(1)
            a, m = calc(arena, entries[i])
            c_all, c_missed = c_all + a, c_missed + m
    logger.info("Oracle acc {}, ({}/{})".format(1- c_missed / c_all, c_missed, c_all))
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
