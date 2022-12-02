import argparse
import sys
import threading
from queue import Queue
from random import shuffle

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import ParameterGrid
from tqdm import tqdm

from egs.cmp_matrix.local.data import App, Arena
from egs.cmp_matrix.local.similarities import similarity, Entry, LEntry, e_key, sim_imp
from src.utils.logger import logger


def calc_sims(arena, row, entry_dict):
    dt = row.date
    arena.move(dt)

    els = []
    sims = []

    def check(e):
        nonlocal els, sims
        v = similarity(e, row, entry_dict)
        els.append(e)
        sims.append(v)

    for e in arena.gl_entries:
        check(e)
    for e in arena.playground.values():
        check(e)

    return {"els": els, "sims": sims}


def find_best(data, params):
    els = data["els"]
    sims = data["sims"]
    b = 0
    res = ""
    for i, s in enumerate(sims):
        v = np.dot(np.array(s), params)
        if v > b:
            b = v
            res = els[i]
    return res.id if res else ""


class Selector:
    def __init__(self, mtrx):
        self.mtrx = mtrx

    def predict(self, X, params):
        res = []
        logger.info("predict called {}".format(params))
        for i in range(len(X)):
            res.append(find_best(self.mtrx[i], params))

        return res

    def get_params(self, params):
        out = np.array(sim_imp, copy=True)
        out[0] = params["name_eq"]
        out[1] = params["name_sim"]
        out[2] = params.get("iban_match", out[2])
        out[3] = params.get("ext_doc", out[3])
        out[4] = params.get("due_date", out[4])
        out[5] = params.get("entry_date", out[5])
        out[6] = params.get("amount_match", out[6])
        out[7] = params.get("has_past", out[7])
        out[8] = params.get("curr_match", out[8])
        out[9] = params.get("payment_match", out[9])
        return out


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
    X = entries
    y = [e.rec_id for e in entries]

    entry_dic = {}
    for e in entries:
        k = e_key(e)
        arr = entry_dic.get(k, [])
        arr.append(e)
        entry_dic[k] = arr

    mtrx = []
    with tqdm(desc="preparinng", total=len(entries)) as pbar:
        for i in range(len(entries)):
            pbar.update(1)
            mtrx.append(calc_sims(arena, entries[i], entry_dic))

    model = Selector(mtrx)

    param_grid = {
        "name_eq": np.linspace(0, 2, num=3),
        "name_sim": np.linspace(0, 2, num=3),
        "iban_match": np.linspace(0, 2, num=3),
        "ext_doc": np.linspace(0, 2, num=3),
        "due_date": np.linspace(0, 2, num=3),
        "entry_date": np.linspace(0, 2, num=3),
        "amount_match": np.linspace(0, 2, num=3),
        "has_past": np.linspace(0, 2, num=3),
        "curr_match": np.linspace(0, 2, num=3),
        "payment_match": np.linspace(0, 2, num=3),
    }
    # run grid search
    pg = ParameterGrid(param_grid)
    pgl = list(pg)
    shuffle(pgl)

    workQ = Queue(maxsize=1)
    resQ = Queue(maxsize=1)

    def work():
        while True:
            p = workQ.get()
            if p is None:
                break
            y_pred = model.predict(X, model.get_params(p))
            logger.info("predicted")
            score = accuracy_score(y[50:], y_pred[50:])
            logger.info("done")
            resQ.put((score, p))
        logger.info("exit work")

    scores = []

    def res_work():
        while True:
            score, p = resQ.get()
            if score is None:
                break
            logger.info("{} - {}".format(score, p))
            print("got result {}\t{}".format(score, p), flush=True)
            scores.append([score, p])
        logger.info("exit res work")

    workers = []

    def start_thread(method):
        thread = threading.Thread(target=method, daemon=True)
        thread.start()
        workers.append(thread)

    start_thread(res_work)
    threads = 6
    for i in range(threads):
        start_thread(work)

    with tqdm(desc="predicting", total=len(pgl)) as pbar:
        for p in pgl:
            pbar.update(1)
            logger.info("put {}".format(p))
            workQ.put(p)
    logger.info("work done")

    for i in range(threads):
        workQ.put(None)
    resQ.put((None, None))

    for w in workers:
        w.join()

    if len(scores) > 0:
        scores.sort(key=lambda e: -e[0])
        logger.info("BEST Value: {}".format(scores[0]))
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
