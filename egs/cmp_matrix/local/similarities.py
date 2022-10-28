import argparse
import sys

import pandas as pd
from tqdm import tqdm

from src.utils.logger import logger
from src.utils.similarity import name_sim


def e_str(p):
    if p != p:
        return ''
    return str(p)


def similarity(ledger, entry):
    res = [ledger]
    nl = e_str(ledger['Name'])
    ne = e_str(entry['Description'])
    res.append(1 if nl.lower() == ne.lower() else 0)
    res.append(name_sim(nl, ne))
    res.append(1 if e_str(ledger['IBAN']) == e_str(entry['IBAN']) else 0)
    return res


def to_str(param):
    return "{}:{} - {} - {}".format(param["Type"], param["No"], param["Name"], param["Due_Date"])


def e_to_str(r):
    return "{} - {} - {}".format(r["Description"], r["Message"], r["Date"])


def main(argv):
    parser = argparse.ArgumentParser(description="Calculates similarity for one item",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file of bank entries")
    parser.add_argument("--ledgers", nargs='?', required=True, help="Ledgers file")
    parser.add_argument("--i", nargs='?', required=True, help="Number of entries file to check")
    args = parser.parse_args(args=argv)

    logger.info("Starting")

    entries = pd.read_csv(args.input, sep=',')
    logger.info("loaded cmp_matrix {} rows".format(len(entries)))
    logger.info("Headers: {}".format(list(entries)))
    logger.info("\n{}".format(entries.head(n=10)))

    ledgers = pd.read_csv(args.ledgers, sep=',')
    logger.info("loaded cmp_matrix {} rows".format(len(ledgers)))
    logger.info("Headers: {}".format(list(ledgers)))
    logger.info("\n{}".format(ledgers.head(n=10)))

    row = entries.iloc[int(args.i)]
    logger.info("Testing: {}".format(e_to_str(row)))

    res = []
    with tqdm(desc="format cmp_matrix", total=len(ledgers)) as pbar:
        for i in range(len(ledgers)):
            pbar.update(1)
            res.append(similarity(ledgers.iloc[i], row))
    res.sort(key=lambda x: sum(x[1:]), reverse=True)
    logger.info("Res:")
    for i, r in enumerate(res[:10]):
        logger.info("\t{} - {}, {}".format(i, to_str(r[0]), r[1:]))
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
