import argparse
import multiprocessing
import pickle
import sys

import pandas as pd
from tqdm import tqdm

from bankmap.data import Entry, App, Arena, LEntry, Ctx
from bankmap.logger import logger
from bankmap.similarity.similarities import prepare_history_map, similarity


class CalcData:
    def __init__(self):
        self.ctx = None
        self.arena = None
        self.entries = None
        self.entry_dic = None


class Feature:
    def __init__(self, entry: Entry, arr_v, arr_it):
        self.rec_id = entry.rec_id
        self.rec_type = entry.rec_type
        self.arr_v = arr_v
        self.arr_it = arr_it


def get_features(ctx, arena, entry: Entry, entry_dic):
    dt = entry.date
    arena.move(dt)
    arr_v = []
    arr_it = []

    def add(_e):
        v = similarity(ctx, _e, entry, entry_dic)
        arr_v.append(v)
        arr_it.append((e.type, e.id))

    for e in arena.gl_entries:
        add(e)
    for e in arena.playground.values():
        add(e)
    return Feature(entry, arr_v, arr_it)


def run(i):
    logger.debug("got job {}".format(i))
    feat = get_features(data.ctx, data.arena, data.entries[i], data.entry_dic)
    logger.debug("done job {}".format(i))
    return feat


def main(argv):
    parser = argparse.ArgumentParser(description="Make similarity features",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file of bank entries")
    parser.add_argument("--ledgers", nargs='?', required=True, help="Ledgers file")
    parser.add_argument("--apps", nargs='?', required=True, help="Applications file")
    parser.add_argument("--out", nargs='?', required=True, help="output features file")
    parser.add_argument("--history", nargs='?', type=int, required=True, help="History in days to look for")
    args = parser.parse_args(args=argv)

    logger.info("Starting")

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

    def init():
        global data
        logger.debug("init")
        data = CalcData()
        data.entries = entries
        data.entry_dic = entry_dic
        l_entries = [LEntry(_l) for _l in ledgers.to_dict('records')]
        apps = [App(_i) for _i in apps_t.to_dict('records')]
        data.arena = Arena(l_entries, apps)
        data.ctx = Ctx(history_days=args.history)
        logger.debug("init ended")

    threads = 12
    with open(args.out, 'wb') as f:
        pickle.dump(len(entries), f, pickle.HIGHEST_PROTOCOL)
        with tqdm("prepare features", total=len(entries)) as pbar:
            with multiprocessing.Pool(threads, initializer=init) as p:
                for res in p.imap(run, [i for i in range(len(entries))]):
                    pickle.dump(res, f, pickle.HIGHEST_PROTOCOL)
                    pbar.update(1)

    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
