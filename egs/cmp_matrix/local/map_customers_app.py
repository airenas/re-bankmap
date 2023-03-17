import argparse
import sys

import pandas as pd

from bankmap.data import LEntry
from bankmap.loaders.apps import load_customer_apps
from bankmap.logger import logger


def main(argv):
    parser = argparse.ArgumentParser(description="Extracts app data for customers",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file")
    parser.add_argument("--ledgers", nargs='?', required=True, help="Input SF file")
    args = parser.parse_args(args=argv)

    logger.info("Starting")
    ledgers = pd.read_csv(args.ledgers, sep=',')
    logger.info("loaded ledgers {} rows".format(len(ledgers)))
    logger.debug("Headers: {}".format(list(ledgers)))
    logger.debug("\n{}".format(ledgers.head(n=10)))
    l_entries = [LEntry(ledgers.iloc[i]) for i in range(len(ledgers))]

    df_out = load_customer_apps(args.input, l_entries)
    df_out.to_csv(sys.stdout, index=False)
    logger.info("wrote {} apps".format(len(df_out)))
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
