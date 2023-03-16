import argparse
import sys

import pandas as pd

from bankmap.logger import logger
from bankmap.transformers.entry import load_bank_recognitions_map, load_entries


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
    docs = pd.read_csv(args.docs_map, sep=',')
    cv_map = {docs.iloc[i]["ID"]: (docs.iloc[i]["Ext_ID"], docs.iloc[i]["Vend_Cust_No"]) for i in range(len(docs))}

    df = load_entries(args.input, ba_map, cv_map)
    df.to_csv(sys.stdout, index=False)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
