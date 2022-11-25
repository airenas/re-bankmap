import argparse
import sys

import pandas as pd
from tqdm import tqdm

from egs.cmp_matrix.local.map_customers import ledger_cols
from egs.cmp_matrix.local.similarities import e_currency, e_str
from src.utils.logger import logger


def is_recognized(param):
    if param or param.strip() != "":
        return True
    return False


def prepare_data(df, names, accounts):
    res = []
    with tqdm("format cmp_matrix", total=len(df)) as pbar:
        for i in range(len(df)):
            pbar.update(1)
            dt = e_str(df['Document_Type'].iloc[i])
            if not dt or dt == "Mokėjimas":
                continue
            _id = df['Vendor_No_'].iloc[i]
            res.append(['Vendor', _id, names.get(_id, ''), accounts.get(_id, ''), df['Document_No_'].iloc[i],
                        df['Due_Date'].iloc[i],
                        df['Document_Date'].iloc[i], df['External_Document_No_'].iloc[i],
                        df['Amount'].iloc[i],
                        e_currency(df['Currency_Code'].iloc[i]),
                        dt])
    return res, ledger_cols


def main(argv):
    parser = argparse.ArgumentParser(description="Extracts cmp_matrix for customers ledger entries",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file prefix for customers")
    args = parser.parse_args(args=argv)

    logger.info("Starting")
    ledgers = pd.read_csv(args.input + "_Ledger_Entries.csv", sep=',')
    logger.info("loaded cmp_matrix {} rows".format(len(ledgers)))
    accounts = pd.read_csv(args.input + "_Bank_Accounts.csv", sep=',')
    logger.info("loaded cmp_matrix {} rows".format(len(accounts)))
    names = pd.read_csv(args.input + "s.csv", sep=',')
    logger.info("loaded cmp_matrix {} rows".format(len(names)))

    # logger.info("Headers: {}".format(list(accounts)))
    names_d = {r['No_']: r['Name'] for _, r in names.iterrows()}
    accounts_d = {r['Vendor_No_']: r['Bank_Account_No_'] for _, r in accounts.iterrows()}

    logger.info("{}".format(names.head(n=10)))
    logger.info("Headers: {}".format(list(ledgers)))
    res, cols = prepare_data(ledgers, names_d, accounts_d)
    df = pd.DataFrame(res, columns=cols)
    df.to_csv(sys.stdout, index=False)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
