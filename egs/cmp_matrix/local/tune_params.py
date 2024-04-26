import argparse
import sys

import numpy as np
from hyperopt import fmin, tpe, hp
from jsonlines import jsonlines
from sklearn.metrics import accuracy_score
from tqdm import tqdm

from bankmap.data import Entry, LEntry, App, Arena, Ctx, use_e2e
from bankmap.history_stats import Stats
from bankmap.logger import logger
from bankmap.similarity.sim_weights import sim_imp, sim_e2e
from bankmap.similarity.similarities import similarity, prepare_history_map, param_names


def calc_sims(ctx, arena, row, entry_dict):
    dt = row.date
    arena.move(dt)
    ctx.stats.move(dt)

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
    def __init__(self, mtrx, ctx):
        self.mtrx = mtrx
        self.ctx = ctx

    def predict(self, X, params):
        res = []
        # logger.info("predict called {}".format(params))
        for i in range(len(X)):
            res.append(find_best(self.mtrx[i], params))

        return res

    def get_params(self, params):
        w = sim_imp
        if self.ctx.use_e2e:
            w = sim_e2e
        out = np.array(w, copy=True)
        for i, v in enumerate(param_names(self.ctx)):
            out[i] = params.get(v, out[i])
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

    entries_t = []
    with jsonlines.open(args.input) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")
            entries_t.append(d)
    logger.info("loaded entries {} rows".format(len(entries_t)))
    entries = [Entry(i) for i in entries_t]

    ledgers = []
    with jsonlines.open(args.ledgers) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")
            ledgers.append(d)
    logger.info("loaded ledgers {} rows".format(len(ledgers)))
    l_entries = [LEntry(i) for i in ledgers]

    apps_t = []
    with jsonlines.open(args.apps) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")
            apps_t.append(d)
    logger.info("loaded apps {} rows".format(len(apps_t)))
    apps = [App(i) for i in apps_t]

    arena = Arena(l_entries, apps)

    entries.sort(key=lambda e: e.date.timestamp() if e.date else 1)
    X_all = [e for e in entries if e.rec_id]
    logger.info("Dropped without cust/vend: {}".format(len(entries) - len(X_all)))
    logger.info(f"Split at {args.split_at}")
    Xv = X_all[args.split_at:]
    X = X_all[:args.split_at]
    y = [e.rec_id for e in X]
    yv = [e.rec_id for e in Xv]
    logger.info("Train set {}, val set: {}".format(len(X), len(Xv)))
    entry_dic = prepare_history_map(entries)

    mtrx = []
    stats = Stats(entries)
    ctx = Ctx(history_days=args.history, stats=stats, use_e2e=use_e2e(l_entries))
    with tqdm(desc="preparing train", total=len(X)) as pbar:
        for i in range(len(X)):
            pbar.update(1)

            mtrx.append(calc_sims(ctx, arena, X[i], entry_dic))

    model = Selector(mtrx, ctx)

    mtrx_v = []
    with tqdm(desc="preparing val", total=len(Xv)) as pbar:
        for i in range(len(Xv)):
            pbar.update(1)
            mtrx_v.append(calc_sims(ctx, arena, Xv[i], entry_dic))

    model_v = Selector(mtrx_v, ctx)

    param_grid = {v: hp.uniform(v, 0, 1) for v in param_names(ctx)}

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
                "found {} - ({} of {} bad), val({} - ({} of {}))".format(bv,
                                                                         len([i for i, x in enumerate(y[args.skip:]) if
                                                                              x != y_pred[args.skip:][i]]),
                                                                         len(y_pred[args.skip:]),
                                                                         vs,
                                                                         len([i for i, x in enumerate(yv) if
                                                                              x != yv_pred[i]]),
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
