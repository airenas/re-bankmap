import argparse
import sys

import pandas as pd
from tqdm import tqdm

from src.utils.logger import logger


def is_recognized(param):
    if param or param.strip() != "":
        return True
    return False


def prepare_data(df):
    res = []
    cols = ['Description', 'Message', 'CdtDbtInd', 'Recognized', 'Mapped', 'Amount', 'Date']
    with tqdm("format data", total=len(df)) as pbar:
        for i in range(len(df)):
            pbar.update(1)
            res.append([df['Description'].iloc[i], df['Message_to_Recipient'].iloc[i], df['N_CdtDbtInd'].iloc[i],
                        is_recognized(df['Recognized_Account_No_'].iloc[i]), df['Recognized_Account_No_'].iloc[i],
                        df['N_Amt'].iloc[i], df['N_BookDt_Dt'].iloc[i]])
    return res, cols


def main(argv):
    parser = argparse.ArgumentParser(description="Extracts data from bank statement entries table",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file")
    args = parser.parse_args(args=argv)

    logger.info("Starting")

    logger.info("loading data {}".format(args.input))
    data = pd.read_csv(args.input, sep=',')
    logger.info("loaded data {} rows".format(len(data)))
    logger.info("{}".format(data.head(n=10)))
    hd = list(data)
    logger.info("Headers: {}".format(hd))
    res, cols = prepare_data(data)
    df = pd.DataFrame(res, columns=cols)
    df.to_csv(sys.stdout, index=False)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
