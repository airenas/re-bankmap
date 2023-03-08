import argparse
import multiprocessing
import sys
import threading
from multiprocessing import Queue

import pandas as pd
from tqdm import tqdm

from egs.cmp_matrix.local.data import App, Arena, LType
from egs.cmp_matrix.local.predict_docs import find_best_docs
from egs.cmp_matrix.local.similarities import similarity, Entry, LEntry, sim_val, e_key
from src.utils.logger import logger


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
    entries.sort(key=lambda e: e.date.timestamp() if e.date else 1)
    entry_dic = {}
    for e in entries:
        k = e_key(e)
        arr = entry_dic.get(k, [])
        arr.append(e)
        entry_dic[k] = arr

    pr_bar = tqdm(desc="predicting", total=len(entries))

    def run(entries, entry_dic, start, queue: Queue):
        logger.info("start thread {}:{}".format(start, start + len(entries)))
        l_entries = [LEntry(ledgers.iloc[i]) for i in range(len(ledgers))]
        apps = [App(apps_t.iloc[i]) for i in range(len(apps_t))]
        arena = Arena(l_entries, apps)
        logger.info("run thread {}:{}".format(start, start + len(entries)))
        for i in range(len(entries)):
            best, sim = get_best_account(arena, entries[i], entry_dic)
            _res = "{}:{}\t{}\t{}".format(best.type.to_s(), best.id if best is not None else "", "", sim)
            queue.put((i+start, _res))
        logger.info("done thread {}:{}".format(start, start + len(entries)))

    workers = []

    def start_thread(method, args):
        wrk = multiprocessing.Process(target=method, daemon=True, args=args)
        wrk.start()
        workers.append(wrk)

    threads = 8
    start, step = 0, int(len(entries) / threads)
    queue = Queue()
    for i in range(threads):
        to = start + step
        if i == threads - 1:
            to = len(entries)
        start_thread(run, (entries[start:to], entry_dic, start, queue))
        start = to

    res = [""] * len(entries)
    def process_res():
        while True:
            _res = queue.get()
            if _res is None:
                return
            pr_bar.update(1)
            i, v = _res
            res[i] = v

    thread = threading.Thread(target=process_res, daemon=True)
    thread.start()

    for w in workers:
        w.join()

    queue.put(None)
    thread.join()

    for r in res:
        print(r)

    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
