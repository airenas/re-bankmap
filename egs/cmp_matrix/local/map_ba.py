import argparse
import sys

from bankmap.loaders.ledgers import load_ba
from bankmap.logger import logger


def main(argv):
    parser = argparse.ArgumentParser(description="Extracts cmp_matrix for bank account entries",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file")
    args = parser.parse_args(args=argv)

    logger.info("Starting")
    df = load_ba(args.input)
    df.to_csv(sys.stdout, index=False)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
