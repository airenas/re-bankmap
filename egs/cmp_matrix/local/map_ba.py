import argparse
import sys

import pandas as pd
from tqdm import tqdm

from egs.cmp_matrix.local.map_customers import ledger_cols
from egs.cmp_matrix.local.data import e_currency
from src.utils.logger import logger


def is_recognized(param):
    if param or param.strip() != "":
        return True
    return False


# ledger_cols = ['Type', 'No', 'Name', 'IBAN', 'Document_No_', 'Due_Date', 'Document_Date', 'ExtDoc', 'Amount']

def prepare_data(df):
    res = []
    with tqdm("format cmp_matrix", total=len(df)) as pbar:
        for i in range(len(df)):
            pbar.update(1)
            _id = df['No_'].iloc[i]
            res.append(['BA', _id, df['Search_Name'].iloc[i], df['IBAN'].iloc[i], '',
                        '',
                        '', '', 0, e_currency(df['Currency_Code'].iloc[i]),
                        'BA'])
    return res, ledger_cols


def main(argv):
    parser = argparse.ArgumentParser(description="Extracts cmp_matrix for bank account entries",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file")
    args = parser.parse_args(args=argv)

    logger.info("Starting")
    ledgers = pd.read_csv(args.input, sep=',')
    logger.info("loaded {} gl rows".format(len(ledgers)))
    logger.info("Headers: {}".format(list(ledgers)))

    res, cols = prepare_data(ledgers)
    df = pd.DataFrame(res, columns=cols)
    df.to_csv(sys.stdout, index=False)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
