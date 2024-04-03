import argparse
import sys

from bankmap.loaders.ledgers import load_vendor_sfs
from bankmap.logger import logger
from bankmap.utils.utils import json_str


def main(argv):
    parser = argparse.ArgumentParser(description="Extracts cmp_matrix for customers ledger entries",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file prefix for vendors")
    args = parser.parse_args(args=argv)

    logger.info("Starting")
    df = load_vendor_sfs(args.input + "LedgerEntries.jsonl", args.input + "BankAccounts.jsonl", args.input + "s.jsonl")
    for d in df:
        print(json_str(d), file=sys.stdout)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
