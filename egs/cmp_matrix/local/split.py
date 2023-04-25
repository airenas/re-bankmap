import argparse
import sys

import pandas as pd

from bankmap.logger import logger


def main(argv):
    parser = argparse.ArgumentParser(description="Predicts similarities for all item",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file of bank entries")
    parser.add_argument("--split", nargs='?', default=3000, type=int, help="Split into train test at pos")
    parser.add_argument("--out_test", nargs='?', required=True, help="Out test file")
    parser.add_argument("--out_train", nargs='?', required=True, help="Out train file")
    args = parser.parse_args(args=argv)

    logger.info("Starting")

    entries = pd.read_csv(args.input, sep=',')
    logger.info("loaded entries {} rows".format(len(entries)))
    train = entries.head(n=args.split)
    test = entries.tail(n=len(entries) - args.split)
    with open(args.out_train, "w") as f:
        train.to_csv(f, index=False)
        logger.info("saved train {} rows".format(len(train)))
    with open(args.out_test, "w") as f:
        test.to_csv(f, index=False)
        logger.info("saved test {} rows".format(len(test)))
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
