import argparse
import json
import sys

import pandas as pd
from sklearn.metrics import accuracy_score

from egs.cmp_matrix.local.similarities import sim_val
from src.utils.logger import logger


def first_word(l1):
    w1 = l1.split("\t")
    return w1[0].strip()


def main(argv):
    parser = argparse.ArgumentParser(description="Compares two files",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--f1", nargs='?', required=True, help="File 1")
    parser.add_argument("--f2", nargs='?', required=True, help="File 2")
    parser.add_argument("--out", nargs='?', required=True, help="Output File")
    parser.add_argument("--skip", nargs='?', default=0, type=int, help="Skip [n] first items in comparison")
    parser.add_argument("--limit", nargs='?', default=0, type=float, help="Limit when to reject making decision")
    args = parser.parse_args(args=argv)

    logger.info("Starting")
    logger.info("File 1: {}".format(args.f1))
    logger.info("File 2: {}".format(args.f2))
    with open(args.f2, 'r') as f2:
        y_pred_l = [line.strip() for line in f2]
    logger.info("loaded predicted {} rows".format(len(y_pred_l)))

    entries = pd.read_csv(args.f1, sep=',')
    logger.info("loaded entries {} rows".format(len(entries)))
    logger.info("Headers: {}".format(list(entries)))
    y_true = entries["RecAccount"].values.tolist()
    y_recognized = entries["Recognized"].values.tolist()

    skip = args.skip
    y_true = y_true[skip:len(y_pred_l)]
    y_pred = [y.split('\t')[0] for y in y_pred_l[skip:]]
    y_pred_v = [json.loads(y.split('\t')[1]) for y in y_pred_l[skip:]]

    y_pred = [x if sim_val(y_pred_v[i]) > args.limit else 'rejected' for i, x in enumerate(y_pred)]

    with open(args.out, 'w') as f:
        for i, y in enumerate(y_true):
            ir = i + skip
            v = y_pred[i]
            vec = y_pred_v[i]
            val = sim_val(vec)
            if v == y and val > args.limit:
                print("{}\t{}\t{}".format(ir, y, 'r' if y_recognized[i] else 'n'), file=f)
            else:
                print("{}\t{}\t{}\t{} <--diff-->\t{}\t{}".format(ir, y, v, 'r' if y_recognized[i] else 'n',
                                                                 vec, val), file=f)

    logger.info("Acc all        : {} ({}/{})".format(accuracy_score(y_true, y_pred),
                                                     sum([1 for i, x in enumerate(y_true) if y_pred[i] != x]),
                                                     len(y_true)))
    y_true_n = [x for x in y_true if str(x) != 'nan']
    y_pred_n = [x for i, x in enumerate(y_pred) if str(y_true[i]) != 'nan']
    logger.info(
        "Acc not empty : {} ({}/{})".format(accuracy_score(y_true_n, y_pred_n),
                                            sum([1 for i, x in enumerate(y_true_n) if y_pred_n[i] != x]),
                                            len(y_true_n)))
    y_true_n = [x for i, x in enumerate(y_true) if
                str(y_true[i]) != 'nan' and y_pred[i] != 'rejected']
    y_pred_n = [x for i, x in enumerate(y_pred) if str(y_true[i]) != 'nan'
                and x != 'rejected']
    logger.info(
        "Acc w/o rejected: {} ({}/{})".format(accuracy_score(y_true_n, y_pred_n),
                                              sum([1 for i, x in enumerate(y_true_n) if y_pred_n[i] != x]),
                                              len(y_true_n)))
    y_true_n = [x for i, x in enumerate(y_true) if not y_recognized[i] and str(y_true[i]) != 'nan']
    y_pred_n = [x for i, x in enumerate(y_pred) if not y_recognized[i] and str(y_true[i]) != 'nan']
    logger.info(
        "Acc not rec before: {} ({}/{})".format(accuracy_score(y_true_n, y_pred_n),
                                                sum([1 for i, x in enumerate(y_true_n) if y_pred_n[i] != x]),
                                                len(y_true_n)))
    y_true_n = [x for i, x in enumerate(y_true) if y_recognized[i] and str(y_true[i]) != 'nan']
    y_pred_n = [x for i, x in enumerate(y_pred) if y_recognized[i] and str(y_true[i]) != 'nan']
    logger.info(
        "Acc rec before: {} ({}/{})".format(accuracy_score(y_true_n, y_pred_n),
                                            sum([1 for i, x in enumerate(y_true_n) if y_pred_n[i] != x]),
                                            len(y_true_n)))
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
