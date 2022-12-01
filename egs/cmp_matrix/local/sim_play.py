import argparse
import sys

import pandas as pd
from tqdm import tqdm

from egs.cmp_matrix.local.predict_play import Arena
from egs.cmp_matrix.local.similarities import Entry, LEntry, App, e_key, similarity, sim_val
from src.utils.logger import logger


def main(argv):
    parser = argparse.ArgumentParser(description="Calculates similarity for one item (with playground)",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file of bank entries")
    parser.add_argument("--ledgers", nargs='?', required=True, help="Ledgers file")
    parser.add_argument("--apps", nargs='?', required=True, help="Applications file")
    parser.add_argument("--i", nargs='?', required=True, help="Number of entries file to check")
    parser.add_argument("--top", nargs='?', default=20, type=int, help="Show the top most similar items")
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

    row = entries[int(args.i)]
    logger.info("Testing bank entry: \n{}".format(entries_t.iloc[int(args.i)]))
    dt = row.date
    logger.info("Entry date: {}".format(dt))
    arena.move(dt)
    res = []

    def check(_e):
        v = similarity(_e, row, entry_dic)
        out = sim_val(v)
        res.append({"i": out, "sim": v, "entry": _e})

    for e in arena.gl_entries:
        check(e)
    for e in arena.playground.values():
        check(e)

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
