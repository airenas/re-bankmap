import argparse
import sys

from jsonlines import jsonlines

from bankmap.logger import logger
from bankmap.utils.utils import json_str


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

    entries = []
    with jsonlines.open(args.input) as reader:
        for (i, d) in enumerate(reader):
            entries.append(d)
    train = entries[:args.split]
    test = []
    if len(entries) > args.split:
        test = entries[args.split:]
    with open(args.out_train, "w") as f:
        for d in train:
            print(json_str(d), file=f)
        logger.info("saved train {} rows".format(len(train)))
    with open(args.out_test, "w") as f:
        for d in test:
            print(json_str(d), file=f)
        logger.info("saved test {} rows".format(len(test)))
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
