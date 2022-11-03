import argparse
import sys

import pandas as pd
from sklearn.metrics import accuracy_score

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
    args = parser.parse_args(args=argv)

    logger.info("Starting")
    logger.info("File 1: {}".format(args.f1))
    logger.info("File 2: {}".format(args.f2))
    with open(args.f2, 'r') as f2:
        y_pred = [line.strip() for line in f2]
    logger.info("loaded predicted {} rows".format(len(y_pred)))

    entries = pd.read_csv(args.f1, sep=',')
    logger.info("loaded entries {} rows".format(len(entries)))
    logger.info("Headers: {}".format(list(entries)))
    y_true = entries["RecAccount"].values.tolist()
    y_true = y_true[:len(y_pred)]

    with open(args.out, 'w') as f:
        for i, y in enumerate(y_true):
            v = y_pred[i].split('\t')
            if v[0] == y:
                print("{}".format(y))
            else:
                print("{}\t{} <--diff-->\t{}".format(y, v[0], v[1] if len(v) > 0 else ""))

    logger.info("Acc all        : {} from {}".format(accuracy_score(y_true, y_pred), len(y_true)))
    y_true_n = [x for x in y_true if str(x) != 'nan']
    y_pred_n = [x for i, x in enumerate(y_pred) if str(y_true[i]) != 'nan']
    logger.info("Acc with values: {} from {}".format(accuracy_score(y_true_n, y_pred_n), len(y_true_n)))

    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
