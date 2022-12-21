import argparse
import sys

import pandas as pd

from egs.cmp_matrix.local.data import Entry, LEntry
from src.utils.logger import logger
from src.utils.similarity import sf_sim


def main(argv):
    parser = argparse.ArgumentParser(description="Shows SF vs messages",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file of bank entries")
    parser.add_argument("--ledgers", nargs='?', required=True, help="Ledgers file")
    args = parser.parse_args(args=argv)

    logger.info("Starting")

    entries_t = pd.read_csv(args.input, sep=',')
    logger.info("loaded entries {} rows".format(len(entries_t)))
    logger.debug("Headers: {}".format(list(entries_t)))
    logger.debug("\n{}".format(entries_t.head(n=10)))
    entries = [Entry(entries_t.iloc[i]) for i in range(len(entries_t))]

    ledgers = pd.read_csv(args.ledgers, sep=',')
    logger.info("loaded ledgers {} rows".format(len(ledgers)))
    logger.debug("Headers: {}".format(list(ledgers)))
    logger.debug("\n{}".format(ledgers.head(n=10)))
    l_entries = [LEntry(ledgers.iloc[i]) for i in range(len(ledgers))]

    sf_map = {e.doc_no: e.ext_doc for e in l_entries if e.doc_no}

    def map(docs):
        docs = docs.split(";")
        res = [sf_map.get(d) for d in docs if d]
        res = [d for d in res if d]
        return res

    for i, e in enumerate(entries):
        target = map(e.doc_ids)
        pt = []
        if len(target) > 0:
            for t in target:
                if t not in e.msg:
                    v = sf_sim(t, e.msg)
                    if v == 0:
                        pt.append(t)
            if len(pt):
                logger.info("{}\t{}\t==> {}".format(i, e.msg, " ".join(pt)))
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
