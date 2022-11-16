import argparse
import csv
import sys

import pandas as pd

from src.utils.logger import logger
from matplotlib import pyplot as plt

def load_data(f):
    logger.info("loading data {}".format(f))
    return pd.read_csv(f, sep=',')


def main(argv):
    parser = argparse.ArgumentParser(description="Inspect data",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--i", nargs='?', required=True, help="Initial data")
    args = parser.parse_args(args=argv)

    logger.info("Starting")
    df = load_data(args.i)
    logger.info("sample data")
    print(df.head(10), sep='\n\n')
    logger.info("info:")
    df.info()
    logger.info("describe:")
    df.describe()
    logger.info("len         {}".format(len(df)))
    logger.info("rec     len {}".format(len(df.query('Recognized'))))
    logger.info("not rec len {}".format(len(df.query('not Recognized'))))
    logger.info("not set target {}".format(len(df[df.RecAccount.isnull()])))


if __name__ == "__main__":
    main(sys.argv[1:])
