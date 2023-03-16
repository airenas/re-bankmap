import argparse
import sys

import numpy as np
import pandas as pd
from tqdm import tqdm

from bankmap.data import Entry, LEntry, App, Arena, LType
from bankmap.logger import logger


def calc(arena, row: Entry):
    docs = set([x for x in row.doc_ids.split(";") if x])
    if len(docs) == 0:
        return 0, 0, 0, []
    dt = row.date
    arena.move(dt)
    found = set()
    cust_vend = ""
    for e in arena.playground.values():
        if e.doc_no in docs:
            found.add(e.doc_no)
            cust_vend = e.id
    select_from = [x for x in arena.playground.values() if x.id == cust_vend]
    missing = [x for x in docs if x not in found]
    return len(docs), len(docs) - len(found), len(select_from), missing


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
    logger.debug("Headers: {}".format(list(entries_t)))
    logger.debug("\n{}".format(entries_t.head(n=10)))
    entries = [Entry(entries_t.iloc[i]) for i in range(len(entries_t))]

    ledgers = pd.read_csv(args.ledgers, sep=',')
    logger.info("loaded ledgers {} rows".format(len(ledgers)))
    logger.debug("Headers: {}".format(list(ledgers)))
    logger.debug("\n{}".format(ledgers.head(n=10)))
    l_entries = [LEntry(ledgers.iloc[i]) for i in range(len(ledgers))]

    apps_t = pd.read_csv(args.apps, sep=',')
    logger.info("loaded apps {} rows".format(len(apps_t)))
    logger.debug("Headers: {}".format(list(apps_t)))
    logger.debug("\n{}".format(apps_t.head(n=10)))
    apps = [App(apps_t.iloc[i]) for i in range(len(apps_t))]

    doc_nrs = set(l.doc_no for l in l_entries)

    arena = Arena(l_entries, apps)

    logger.info(
        "GL, BA count: {}".format(len([l for l in filter(lambda x: x.type in [LType.GL, LType.BA], l_entries)])))
    logger.info(
        "Vend SF count: {}".format(len([l for l in filter(lambda x: x.type in [LType.VEND], l_entries)])))
    logger.info(
        "Vend SF closed count: {}".format(
            len([l for l in filter(lambda x: x.type in [LType.VEND] and x.closed_date, l_entries)])))
    logger.info(
        "Cust SF count: {}".format(len([l for l in filter(lambda x: x.type in [LType.CUST], l_entries)])))
    logger.info(
        "Cust SF closed count: {}".format(
            len([l for l in filter(lambda x: x.type in [LType.CUST] and x.closed_date, l_entries)])))

    entries.sort(key=lambda e: e.date.timestamp() if e.date else 1)

    c_all, c_missed = 0, 0
    c_froms, not_founds, not_founds_pl = [], [], []
    with tqdm(desc="calc oracle", total=len(entries)) as pbar:
        for i in range(len(entries)):
            pbar.update(1)
            a, m, select_from, missing = calc(arena, entries[i])
            c_all, c_missed = c_all + a, c_missed + m
            if m > 0:
                c_froms.append(select_from)
            for nf in missing:
                not_founds_pl.append(nf)
                if nf not in doc_nrs:
                    not_founds.append(nf)
    logger.info("Oracle acc {}, ({}/{})".format(1 - c_missed / c_all, c_missed, c_all))
    logger.info("Average select from {}, std: {}, max {}".format(np.average(c_froms), np.std(c_froms), np.max(c_froms)))
    logger.info("Not founds in pl {}, all {}".format(len(not_founds_pl), len(not_founds)))
    for nf in not_founds:
        logger.debug("Not FOUND {}".format(nf))
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
