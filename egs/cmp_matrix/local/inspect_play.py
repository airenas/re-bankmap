import argparse
import datetime
import sys

import pandas as pd

from egs.cmp_matrix.local.data import LEntry, App, to_date
from egs.cmp_matrix.local.predict_play import Arena
from src.utils.logger import logger


def main(argv):
    parser = argparse.ArgumentParser(description="Inspect playground",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--ledgers", nargs='?', required=True, help="Ledgers file")
    parser.add_argument("--apps", nargs='?', required=True, help="Applications file")
    parser.add_argument("--c", nargs='?', required=False, help="Customer")
    parser.add_argument("--doc", nargs='?', required=False, help="Doc to inspect")
    parser.add_argument("--date", nargs='?', required=False, help="Date to inspect to")
    args = parser.parse_args(args=argv)

    logger.info("Starting")

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

    if args.date:
        dt = to_date(args.date)
    else:
        dt = datetime.datetime.now()
    logger.info("Date: {}".format(dt))
    if args.c:
        arena.add_cust(args.c)
    if args.doc:
        arena.add_doc(args.doc)

    arena.move(dt)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
