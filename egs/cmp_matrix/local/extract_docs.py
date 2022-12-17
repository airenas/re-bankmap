import argparse
import sys

import pandas as pd
from tqdm import tqdm

from egs.cmp_matrix.local.data import e_str
from src.utils.logger import logger


def main(argv):
    parser = argparse.ArgumentParser(description="Extracts external doc -> internal docs data",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", help="Customers applications file")
    parser.add_argument("--name", help="Internal ID field name")
    args = parser.parse_args(args=argv)

    logger.info("Starting")

    res = {}
    logger.info("loading entries {}".format(args.input))
    df = pd.read_csv(args.input, sep=',')
    logger.info("loaded entries {} rows".format(len(df)))
    logger.info("{}".format(df.head(n=10)))
    logger.info("Headers: {}".format(list(df)))

    with tqdm("read entries", total=len(df)) as pbar:
        for i in range(len(df)):
            pbar.update(1)
            id = e_str(df['Statement_External_Document_No_'].iloc[i])
            iid = e_str(df['Applied_'+args.name+'_Document_No_'].iloc[i])
            ra = res.get(id, set())
            ra.add(iid)
            res[id] = ra
    resc = [[k, ";".join(v)] for k, v in res.items()]
    df = pd.DataFrame(resc, columns=["ID", "Ext_ID"])
    df.to_csv(sys.stdout, index=False)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
