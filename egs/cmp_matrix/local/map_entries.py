import argparse
import sys

from jsonlines import jsonlines

from bankmap.loaders.entries import load_bank_recognitions_map, load_entries
from bankmap.logger import logger
from bankmap.utils.utils import json_str


def main(argv):
    parser = argparse.ArgumentParser(description="Extracts cmp_matrix from bank statement entries table",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file")
    parser.add_argument("--input_map", nargs='?', required=True, help="Customers mapping file")
    parser.add_argument("--docs_map", nargs='?', required=True, help="Docs map file")
    args = parser.parse_args(args=argv)

    logger.info("Starting")
    ba_map = load_bank_recognitions_map(args.input_map)
    logger.info("loading docs map {}".format(args.docs_map))
    cv_map = {}
    with jsonlines.open(args.docs_map) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")
            cv_map[d["id"]] = (d["ext_id"], d["cv_number"])  # TODO check ext_id is OK or is it changes with id

    df = load_entries(args.input, ba_map, cv_map)
    for v in df:
        print(json_str(v), file=sys.stdout)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
