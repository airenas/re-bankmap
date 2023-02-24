import argparse
import sys

import pandas as pd
from tqdm import tqdm

from egs.cmp_matrix.local.data import e_float, e_str, e_currency, to_date
from src.utils.logger import logger


def is_recognized(param):
    if param or param.strip() != "":
        if param != "91":  # special clients ID //todo workaround
            return True
    return False


def iban(p):
    if p["N_ND_TD_RP_DbtrAcct_Id_IBAN"] != p["N_ND_TD_RP_DbtrAcct_Id_IBAN"]:
        return p["N_ND_TD_RP_CdtrAcct_Id_IBAN"]
    return p["N_ND_TD_RP_DbtrAcct_Id_IBAN"]


def prepare_data(df, map, dm):
    res = []
    cols = ['Description', 'Message', 'CdtDbtInd', 'Amount', 'Date', 'IBAN', 'E2EId',
            'RecAccount', 'RecDoc', 'Recognized', 'Currency', 'Docs', 'DocNo']
    found = set()
    with tqdm("read entries", total=len(df)) as pbar:
        for i in range(len(df)):
            pbar.update(1)
            ext_id = e_str(df['External_Document_No_'].iloc[i])
            if ext_id in found:
                continue
            found.add(ext_id)
            rec_no, rec = e_str(df['Recognized_Account_No_'].iloc[i]), True
            if not is_recognized(rec_no):
                rec_no, rec = map.get(ext_id, ""), False

            res.append([df['Description'].iloc[i], df['Message_to_Recipient'].iloc[i], df['N_CdtDbtInd'].iloc[i],
                        e_float(df['N_Amt'].iloc[i]), df['N_BookDt_Dt'].iloc[i], iban(df.iloc[i]),
                        df['N_ND_TD_Refs_EndToEndId'].iloc[i],
                        rec_no,
                        df['Recognized_Document_No_'].iloc[i], rec,
                        e_currency(df['Acct_Ccy'].iloc[i]),
                        dm.get(ext_id, ""),
                        df['External_Document_No_'].iloc[i]])
    return res, cols


def main(argv):
    parser = argparse.ArgumentParser(description="Extracts cmp_matrix from bank statement entries table",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file")
    parser.add_argument("--input_map", nargs='?', required=True, help="Customers mapping file")
    parser.add_argument("--docs_map", nargs='?', required=True, help="Docs map file")
    args = parser.parse_args(args=argv)

    logger.info("Starting")

    logger.info("loading cmp_matrix {}".format(args.input_map))
    data = pd.read_csv(args.input_map, sep=',')
    logger.info("loaded input_map {} rows".format(len(data)))
    logger.info("{}".format(data.head(n=10)))
    logger.info("Headers: {}".format(list(data)))
    map = {}
    with tqdm("read mappings", total=len(data)) as pbar:
        for i in range(len(data)):
            pbar.update(1)
            map[e_str(data['Statement_External_Document_No_'].iloc[i])] = e_str(data['Bal__Account_No_'].iloc[i])

    logger.info("loading entries {}".format(args.input))
    data = pd.read_csv(args.input, sep=',')
    logger.info("loaded entries {} rows".format(len(data)))
    logger.info("{}".format(data.head(n=10)))
    hd = list(data)
    logger.info("Headers: {}".format(hd))
    logger.info("loading docs map {}".format(args.docs_map))
    docs = pd.read_csv(args.docs_map, sep=',')
    dm = {docs.iloc[i]["ID"]: docs.iloc[i]["Ext_ID"] for i in range(len(docs))}
    res, cols = prepare_data(data, map, dm)

    # stable sort by date
    sr = [v for v in enumerate(res)]
    sr.sort(key=lambda e: (to_date(e[1][4]).timestamp(), e[0]))
    res = [v[1] for v in sr]

    df = pd.DataFrame(res, columns=cols)
    df.to_csv(sys.stdout, index=False)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
