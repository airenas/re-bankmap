import argparse
import sys

import numpy as np
import pandas as pd
from hyperopt import fmin, tpe, hp
from sklearn.metrics import accuracy_score
from tqdm import tqdm

from bankmap.data import Entry, LEntry, App, Arena, Ctx
from bankmap.logger import logger
from bankmap.similarity.similarities import similarity, sim_imp, e_key, prepare_history_map


def calc_sims(ctx, arena, row, entry_dict):
    dt = row.date
    arena.move(dt)

    els = []
    sims = []

    def check(e):
        nonlocal els, sims
        v = similarity(ctx, e, row, entry_dict)
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
        # logger.info("predict called {}".format(params))
        for i in range(len(X)):
            res.append(find_best(self.mtrx[i], params))

        return res

    def get_params(self, params):
        out = np.array(sim_imp, copy=True)
        out[0] = params["name_eq"]
        out[1] = params["name_sim"]
        out[2] = params.get("iban_match", out[2])
        out[3] = params.get("ext_doc", out[3])
        out[4] = params.get("ext_doc_sim", out[3])
        out[5] = params.get("due_date", out[4])
        out[6] = params.get("entry_date", out[5])
        out[7] = params.get("amount_match", out[6])
        out[8] = params.get("has_past", out[7])
        out[9] = params.get("curr_match", out[8])
        out[10] = params.get("payment_match", out[9])
        return out


def main(argv):
    parser = argparse.ArgumentParser(description="Predicts similarities for all item",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file of bank entries")
    parser.add_argument("--ledgers", nargs='?', required=True, help="Ledgers file")
    parser.add_argument("--apps", nargs='?', required=True, help="Applications file")
    parser.add_argument("--skip", nargs='?', default=50, type=int, help="Skip initial items for evaluation")
    parser.add_argument("--split_at", nargs='?', default=3000, type=int, help="Skip train/val at pos")
    parser.add_argument("--out", nargs='?', required=True, help="Out file")
    parser.add_argument("--history", nargs='?', type=int, required=True, help="History in days to look for")
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
    X_all = [e for e in entries if e.rec_id]
    logger.info("Dropped without cust/vend: {}".format(len(entries) - len(X_all)))
    Xv = X_all[args.split_at:]
    X = X_all[:args.split_at]
    y = [e.rec_id for e in X]
    yv = [e.rec_id for e in Xv]
    logger.info("Train set {}, val set: {}".format(len(X), len(Xv)))
    entry_dic = prepare_history_map(entries)

    mtrx = []
    ctx = Ctx(history_days=args.history)
    with tqdm(desc="preparing train", total=len(X)) as pbar:
        for i in range(len(X)):
            pbar.update(1)
            mtrx.append(calc_sims(ctx, arena, X[i], entry_dic))

    model = Selector(mtrx)

    mtrx_v = []
    with tqdm(desc="preparing val", total=len(Xv)) as pbar:
        for i in range(len(Xv)):
            pbar.update(1)
            mtrx_v.append(calc_sims(ctx, arena, Xv[i], entry_dic))

    model_v = Selector(mtrx_v)

    param_grid = {
        "name_eq": hp.uniform("name_eq", 0, 1),
        "name_sim": hp.uniform("name_sim", 0, 1),
        "iban_match": hp.uniform("iban_match", 0, 1),
        "ext_doc": hp.uniform("ext_doc", 0, 1),
        "ext_doc_sim": hp.uniform("ext_doc_sim", 0, 1),
        "due_date": hp.uniform("due_date", 0, 1),
        "entry_date": hp.uniform("entry_date", 0, 1),
        "amount_match": hp.uniform("amount_match", 0, 1),
        "has_past": hp.uniform("has_past", 0, 1),
        "curr_match": hp.uniform("curr_match", 0, 1),
        "payment_match": hp.uniform("payment_match", 0, 1),
    }
    scores = []

    f = open(args.out, "w")
    bv = 0

    def estimate(p):
        nonlocal bv
        # logger.info("start {}".format(p))
        pa = model.get_params(p)
        y_pred = model.predict(X, pa)
        score = accuracy_score(y[args.skip:], y_pred[args.skip:])
        scores.append([score, pa])
        print("{}\t{}".format(score, ', '.join(str(x) for x in pa)), flush=True, file=f)
        if bv < score:
            bv = score
            yv_pred = model_v.predict(Xv, pa)
            vs = accuracy_score(yv, yv_pred)
            logger.info(
                "found {} - ({} of {} bad), val({} - ({} of {}))".
                    format(bv,
                           len([i for i, x in enumerate(y[args.skip:]) if x != y_pred[args.skip:][i]]),
                           len(y_pred[args.skip:]),
                           vs,
                           len([i for i, x in enumerate(yv) if x != yv_pred[i]]),
                           len(yv)))
        return 1 - score

    best = fmin(fn=estimate,
                space=param_grid,
                algo=tpe.suggest,
                max_evals=10000)
    logger.info(best)

    if len(scores) > 0:
        scores.sort(key=lambda e: -e[0])
        logger.info("BEST Value: {}".format(scores[0]))
    f.close()
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
