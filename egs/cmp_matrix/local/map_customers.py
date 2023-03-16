import argparse
import sys

import pandas as pd
from tqdm import tqdm

from bankmap.data import e_float, e_currency, e_date, e_str, MapType
from bankmap.logger import logger


def is_recognized(param):
    if param or param.strip() != "":
        return True
    return False


ledger_cols = ['Type', 'No', 'Name', 'IBAN', 'Document_No', 'Due_Date', 'Document_Date', 'ExtDoc', 'Amount',
               'Currency', 'Document_Type', 'Closed_Date', 'Map_Type']


def prepare_data(df, c_data, accounts):
    res = []
    with tqdm("format cmp_matrix", total=len(df)) as pbar:
        for i in range(len(df)):
            pbar.update(1)
            dt = e_str(df['Document_Type'].iloc[i])
            if not dt or dt == "Mokėjimas":
                continue
            _id = df['Customer_No_'].iloc[i]
            cd = c_data[_id]
            res.append(['Customer', _id, cd[0], accounts.get(_id, ''), df['Document_No_'].iloc[i],
                        df['Due_Date'].iloc[i], df['Document_Date'].iloc[i],
                        df['External_Document_No_'].iloc[i],
                        e_float(df['Amount'].iloc[i]),
                        e_currency(df['Currency_Code'].iloc[i]),
                        dt,
                        e_date(df['ClosedAtDate'].iloc[i]), cd[1].to_s()])
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
    c_data = {r['No_']: (r['Name'], MapType.from_s(r['Application_Method'])) for _, r in names.iterrows()}
    accounts_d = {r['Customer_No_']: r['Bank_Account_No_'] for _, r in accounts.iterrows()}

    logger.info("{}".format(names.head(n=10)))
    logger.info("Headers: {}".format(list(ledgers)))
    res, cols = prepare_data(ledgers, c_data, accounts_d)
    df = pd.DataFrame(res, columns=cols)
    df.to_csv(sys.stdout, index=False)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
