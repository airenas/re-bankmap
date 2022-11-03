import argparse
import csv
import sys

import pandas as pd

from src.utils.logger import logger
from matplotlib import pyplot as plt

def load_data(f):
    logger.info("loading data {}".format(f))
    columns = ['eq_name', 'name_sim', 'eq_iban', 'doc_in_msg', 'till_due_date', 'after_doc_date', 'amount_diff',
               'y_same']
    return pd.read_csv(f, sep=',', header=None, quotechar=None, quoting=csv.QUOTE_NONE, names=columns)


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
    plt.hist(df['name_sim'], bins=50)
    plt.show()
    plt.hist(df['till_due_date'], bins=50)
    plt.show()
    plt.hist(df['amount_diff'], bins=50)
    plt.show()
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
