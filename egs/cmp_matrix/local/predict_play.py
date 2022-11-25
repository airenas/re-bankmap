import argparse
import math
import sys
from datetime import timedelta

import pandas as pd
from tqdm import tqdm

from egs.cmp_matrix.local.similarities import similarity, Entry, LEntry, sim_val, e_key, LType, App
from src.utils.logger import logger


class Arena:
    def __init__(self, l_entries, apps):
        self.l_entries = l_entries
        self.gl_entries = [l for l in filter(lambda x: x.type in [LType.GL, LType.BA], l_entries)]
        self.entries = [l for l in filter(lambda x: x.type in [LType.CUST, LType.VEND], l_entries)]
        self.apps = apps
        self.date = None
        logger.info("GL, BA count: {}".format(len(self.gl_entries)))
        logger.info("L count     : {}".format(len(self.entries)))
        logger.info("Apps count  : {}".format(len(self.apps)))
        self.entries.sort(key=lambda e: e.doc_date.timestamp() if e.doc_date else 1)
        self.apps.sort(key=lambda e: e.apply_date.timestamp() if e.apply_date else 1)
        self.date = self.entries[0].doc_date - timedelta(days=1)
        self.playground = {}
        self.from_entry, self.from_apps = 0, 0
        logger.info("Start date  : {}".format(self.date))

    def move(self, dt):
        if self.date < dt:
            logger.info("Move to date  : {}".format(dt))
            while self.from_entry < len(self.entries):
                entry = self.entries[self.from_entry]
                if entry.doc_date > dt:
                    break
                logger.debug("Add  : {} {}".format(entry.doc_no, entry.to_str()))
                self.playground[entry.doc_no] = entry
                self.from_entry += 1
            while self.from_apps < len(self.apps):
                app = self.apps[self.from_apps]
                if app.apply_date >= dt:
                    break
                entry = self.playground.get(app.doc_no, None)
                if entry is not None:
                    if math.isclose(app.remaining, 0):
                        logger.debug("Drop: {} {}".format(entry.doc_no, entry.to_str()))
                        del self.playground[app.doc_no]
                    else:
                        logger.info("Change amount {}: from {} to {}".format(app.doc_no, entry.amount, app.remaining))
                        entry.amount = app.remaining
                else:
                    logger.info("Not found {}: {}".format(app.doc_no, app.to_str()))
                self.from_apps += 1
            logger.info("Items to compare : {}".format(len(self.playground)))
            self.date = dt
        else:
            logger.debug("Up to date  : {}".format(dt))


def get_best_account(arena, row, entry_dict):
    bv, be, b = -1, None, []
    dt = row.date
    arena.move(dt)

    def check(e):
        nonlocal bv, be, b
        v = similarity(e, row, entry_dict)
        out = sim_val(v)
        if bv < out:
            # logger.info("Found better: {} - {}".format(v[1:], out))
            bv = out
            b = v
            be = e

    for e in arena.gl_entries:
        check(e)
    for e in arena.playground.values():
        check(e)

    return be, b


def main(argv):
    parser = argparse.ArgumentParser(description="Predicts similarities for all item",
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

    entry_dic = {}
    for e in entries:
        k = e_key(e)
        arr = entry_dic.get(k, [])
        arr.append(e)
        entry_dic[k] = arr

    with tqdm(desc="predicting", total=len(entries)) as pbar:
        for i in range(len(entries)):
            pbar.update(1)
            best, sim = get_best_account(arena, entries[i], entry_dic)
            print("{}\t{}".format(best.id if best is not None else "", sim))
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
