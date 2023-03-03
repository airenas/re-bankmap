import argparse
import sys

import pandas as pd
from tqdm import tqdm

from egs.cmp_matrix.local.data import e_currency, LEntry
from egs.cmp_matrix.local.map_customers_app import app_cols
from src.utils.logger import logger


def prepare_data(df, l_map):
    res = []
    with tqdm("format data", total=len(df)) as pbar:
        for i in range(len(df)):
            doc = df['Document_No_'].iloc[i]
            cv_no = l_map.get(doc, "")
            pbar.update(1)
            if cv_no:
                res.append(['Vendor', df['Application_Created_Date'].iloc[i],
                            e_currency(df['Application_Amount'].iloc[i]),
                            e_currency(df['Remaining_Amount'].iloc[i]),
                            doc, cv_no
                            ])
    return res, app_cols


def main(argv):
    parser = argparse.ArgumentParser(description="Extracts app data for customers",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file")
    parser.add_argument("--ledgers", nargs='?', required=True, help="Input SF file")
    args = parser.parse_args(args=argv)

    logger.info("Starting")
    df = pd.read_csv(args.input, sep=',')
    logger.info("loaded apps {} rows".format(len(df)))
    logger.info("Headers: {}".format(list(df)))

    ledgers = pd.read_csv(args.ledgers, sep=',')
    logger.info("loaded ledgers {} rows".format(len(ledgers)))
    logger.debug("Headers: {}".format(list(ledgers)))
    logger.debug("\n{}".format(ledgers.head(n=10)))
    l_entries = [LEntry(ledgers.iloc[i]) for i in range(len(ledgers))]
    l_map = {l.doc_no: l.id for l in l_entries}

    res, cols = prepare_data(df, l_map)
    df = pd.DataFrame(res, columns=cols)
    df.to_csv(sys.stdout, index=False)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
