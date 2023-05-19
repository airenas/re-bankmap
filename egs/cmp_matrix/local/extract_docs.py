import argparse
import sys

import pandas as pd

from bankmap.loaders.entries import load_docs_map
from bankmap.logger import logger


def main(argv):
    parser = argparse.ArgumentParser(description="Extracts external doc -> internal docs data",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", help="Customers applications file")
    parser.add_argument("--name", help="Internal ID field name")
    args = parser.parse_args(args=argv)

    logger.info("Starting")

    res = load_docs_map(args.input, args.name)
    resc = [[k, ";".join(v[0]), v[1]] for k, v in res.items()]
    df = pd.DataFrame(resc, columns=["ID", "Ext_ID", "Vend_Cust_No"])
    df.to_csv(sys.stdout, index=False)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
