import argparse
import multiprocessing
import sys

import pandas as pd
from tqdm import tqdm

from bankmap.data import LEntry, App, Arena, Entry, Ctx
from bankmap.logger import logger
from bankmap.similarity.similarities import similarity, sim_val, prepare_history_map


class CalcData:
    def __init__(self):
        self.ctx = None
        self.arena = None
        self.entries = None
        self.entry_dic = None


def get_best_account(ctx, arena, row, entry_dict):
    bv, be, b = -1, None, []
    dt = row.date
    arena.move(dt)

    def check(e):
        nonlocal bv, be, b
        v = similarity(ctx, e, row, entry_dict)
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


def run(i):
    best, sim = get_best_account(data.ctx, data.arena, data.entries[i], data.entry_dic)
    res = "{}:{}\t{}\t{}".format(best.type.to_s(), best.id if best is not None else "", "", sim)
    return res


def main(argv):
    parser = argparse.ArgumentParser(description="Predicts similarities for all item",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file of bank entries")
    parser.add_argument("--ledgers", nargs='?', required=True, help="Ledgers file")
    parser.add_argument("--apps", nargs='?', required=True, help="Applications file")
    parser.add_argument("--history", nargs='?', type=int, required=True, help="History in days to look for")
    args = parser.parse_args(args=argv)

    logger.info("Starting")
    logger.info("history {} days".format(args.history))

    entries_t = pd.read_csv(args.input, sep=',')
    logger.info("loaded entries {} rows".format(len(entries_t)))
    logger.debug("Headers: {}".format(list(entries_t)))
    logger.debug("\n{}".format(entries_t.head(n=10)))

    ledgers = pd.read_csv(args.ledgers, sep=',')
    logger.info("loaded ledgers {} rows".format(len(ledgers)))
    logger.debug("Headers: {}".format(list(ledgers)))
    logger.debug("\n{}".format(ledgers.head(n=10)))

    apps_t = pd.read_csv(args.apps, sep=',')
    logger.info("loaded apps {} rows".format(len(apps_t)))
    logger.debug("Headers: {}".format(list(apps_t)))
    logger.debug("\n{}".format(apps_t.head(n=10)))

    entries = [Entry(entries_t.iloc[i]) for i in range(len(entries_t))]
    entry_dic = prepare_history_map(entries)
    logger.info("init history entries")

    def init():
        global data
        logger.info("init")
        data = CalcData()
        data.entries = entries
        data.entry_dic = entry_dic
        l_entries = [LEntry(_l) for _l in ledgers.to_dict('records')]
        apps = [App(_i) for _i in apps_t.to_dict('records')]
        data.arena = Arena(l_entries, apps)
        data.ctx = Ctx(history_days=args.history)
        logger.info("init ended")

    threads = 12
    with multiprocessing.Pool(threads, initializer=init) as p:
        q = p.map(run, [i for i in range(len(entries))])

    with tqdm("predicting", total=len(q)) as pbar:
        for res in q:
            print(res)
            pbar.update(1)

    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
