import argparse
import json
import sys

from bankmap.loaders.entries import DateTimeEncoder
from bankmap.loaders.ledgers import load_gls
from bankmap.logger import logger


def main(argv):
    parser = argparse.ArgumentParser(description="Extracts cmp_matrix for gl entries",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file for gl")
    args = parser.parse_args(args=argv)

    df = load_gls(args.input)
    for d in df:
        print(json.dumps(d, cls=DateTimeEncoder), file=sys.stdout)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
