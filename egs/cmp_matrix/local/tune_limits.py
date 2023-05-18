import argparse
import json
import sys

import pandas as pd

from bankmap.data import e_str, LType
from bankmap.logger import logger
from bankmap.similarity.similarities import sim_val
from bankmap.tune.tune import Cmp


def calc_limits(cmps, params):
    res = {}
    if len(cmps) == 0:
        res = {v: 1.5 for v in params}
    err, count = 0, 0
    for c in cmps:
        count += 1
        if not c.correct:
            err += 1
            v = (count - err) / count
            pv = 1
            for p in params:
                if pv >= v > p:
                    res[p] = c.value
                    break
                pv = p
        elif err == 0:
            for p in params:
                if p == 1:
                    res[p] = c.value
                    break
    return res


def print_limits(lims):
    for k, v in lims.items():
        logger.info("{}   :{}".format(k, v))


def main(argv):
    parser = argparse.ArgumentParser(description="Tunes rejection limits",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--f1", nargs='?', required=True, help="File 1")
    parser.add_argument("--f2", nargs='?', required=True, help="File 2")
    parser.add_argument("--out", nargs='?', required=True, help="Output File")
    parser.add_argument("--skip", nargs='?', default=0, type=int, help="Skip [n] first items in comparison")
    args = parser.parse_args(args=argv)

    logger.info("Starting")
    logger.info("File 1: {}".format(args.f1))
    logger.info("File 2: {}".format(args.f2))
    with open(args.f2, 'r') as f2:
        y_pred_l = [line.strip() for line in f2]
    logger.info("loaded predicted {} rows".format(len(y_pred_l)))

    df = pd.read_csv(args.f1, sep=',')
    entries = df.to_dict('records')
    skip = args.skip
    entries = entries[skip:len(y_pred_l)]
    y_pred_l = y_pred_l[skip:]
    cmps = []
    for i, e in enumerate(entries):
        type_true = e_str(e["RecType"])
        account_true = e_str(e["RecAccount"])
        if type_true:
            arr = y_pred_l[i].split('\t')
            type_pred, account_pred = arr[0].split(":", 1)
            sims = json.loads(arr[2])
            v = sim_val(sims)
            cmps.append(Cmp(_type=type_pred, value=v, correct=type_pred == type_true and account_pred == account_true))

    cmps.sort(key=lambda item: (-item.value, item.correct))
    bars = [1, 0.995, 0.99, 0.95, 0.90, 0.5]
    lims = calc_limits(cmps, bars)
    print_limits(lims)
    logger.info(LType.CUST.to_s())
    lims = calc_limits([c for c in cmps if c.type == LType.CUST.to_s()], bars)
    print_limits(lims)
    logger.info(LType.VEND.to_s())
    lims = calc_limits([c for c in cmps if c.type == LType.VEND.to_s()], bars)
    print_limits(lims)
    logger.info(LType.BA.to_s())
    lims = calc_limits([c for c in cmps if c.type == LType.BA.to_s()], bars)
    print_limits(lims)
    logger.info(LType.GL.to_s())
    lims = calc_limits([c for c in cmps if c.type == LType.GL.to_s()], bars)
    print_limits(lims)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
