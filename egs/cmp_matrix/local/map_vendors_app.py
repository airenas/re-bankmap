import argparse
import sys

import pandas as pd
from tqdm import tqdm

from egs.cmp_matrix.local.map_customers_app import app_cols
from egs.cmp_matrix.local.data import e_currency
from src.utils.logger import logger


def prepare_data(df):
    res = []
    with tqdm("format data", total=len(df)) as pbar:
        for i in range(len(df)):
            pbar.update(1)
            res.append(['Vendor', df['Vend_Posting_Date'].iloc[i],
                        e_currency(df['Applied_Vend_Purchase__LCY_'].iloc[i]),
                        e_currency(df['Applied_Vend_Remaining_Amount'].iloc[i]),
                        df['Applied_Vend_Document_No_'].iloc[i],
                        df['Statement_External_Document_No_'].iloc[i],
                        df['Vend_Vendor_No_'].iloc[i],
                        df['Vend_Vendor_Name'].iloc[i]
                        ])
    return res, app_cols


def main(argv):
    parser = argparse.ArgumentParser(description="Extracts app data for customers",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file")
    args = parser.parse_args(args=argv)

    logger.info("Starting")
    df = pd.read_csv(args.input, sep=',')
    logger.info("loaded apps {} rows".format(len(df)))

    logger.info("Headers: {}".format(list(df)))
    res, cols = prepare_data(df)
    df = pd.DataFrame(res, columns=cols)
    df.to_csv(sys.stdout, index=False)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
