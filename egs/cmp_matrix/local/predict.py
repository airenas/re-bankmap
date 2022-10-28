import argparse
import sys

import pandas as pd
from tqdm import tqdm

from egs.cmp_matrix.local.similarities import similarity
from src.utils.logger import logger


def get_best_account(ledgers, row):
    bv, b = 0, None
    for i in range(len(ledgers)):
        v = similarity(ledgers.iloc[i], row)
        if bv < sum(v[1:]):
            bv = sum(v[1:])
            b = v[0]
    return b


def main(argv):
    parser = argparse.ArgumentParser(description="Predicts similarities for all item",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file of bank entries")
    parser.add_argument("--ledgers", nargs='?', required=True, help="Ledgers file")
    args = parser.parse_args(args=argv)

    logger.info("Starting")

    entries = pd.read_csv(args.input, sep=',')
    logger.info("loaded cmp_matrix {} rows".format(len(entries)))
    logger.info("Headers: {}".format(list(entries)))
    logger.info("\n{}".format(entries.head(n=10)))

    ledgers = pd.read_csv(args.ledgers, sep=',')
    logger.info("loaded cmp_matrix {} rows".format(len(ledgers)))
    logger.info("Headers: {}".format(list(ledgers)))
    logger.info("\n{}".format(ledgers.head(n=10)))

    with tqdm(desc="predicting", total=len(entries)) as pbar:
        for i in range(len(entries)):
            pbar.update(1)
            best = get_best_account(ledgers, entries.iloc[i])

            print("{}".format(best["No"] if best is not None else ""))
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
