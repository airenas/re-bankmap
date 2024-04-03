import argparse
import sys

from jsonlines import jsonlines

from bankmap.data import LEntry
from bankmap.loaders.apps import load_apps
from bankmap.logger import logger
from bankmap.utils.utils import json_str


def main(argv):
    parser = argparse.ArgumentParser(description="Extracts app data for customers",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file")
    parser.add_argument("--ledgers", nargs='?', required=True, help="Input SF file")
    args = parser.parse_args(args=argv)

    logger.info("Starting")
    ledgers = []
    with jsonlines.open(args.ledgers) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")
            ledgers.append(d)
    logger.info("loaded ledgers {} rows".format(len(ledgers)))
    l_entries = [LEntry(l) for l in ledgers]

    df_out = load_apps(args.input, l_entries, "Customer")
    for d in df_out:
        print(json_str(d), file=sys.stdout)
    logger.info("wrote {} apps".format(len(df_out)))
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
