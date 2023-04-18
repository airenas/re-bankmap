import argparse
import sys

import pandas as pd
from tqdm import tqdm

from bankmap.data import App, LEntry, Entry
from bankmap.data import Arena, LType
from bankmap.logger import logger
from bankmap.predict.docs import find_best_docs


def main(argv):
    parser = argparse.ArgumentParser(description="Predicts similarities for all item",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file of bank entries")
    parser.add_argument("--ledgers", nargs='?', required=True, help="Ledgers file")
    parser.add_argument("--apps", nargs='?', required=True, help="Applications file")
    parser.add_argument("--pred", nargs='?', required=True, help="Cust/Vend predictions")
    args = parser.parse_args(args=argv)

    logger.info("Starting")

    entries_t = pd.read_csv(args.input, sep=',')
    logger.info("loaded entries {} rows".format(len(entries_t)))
    logger.debug("Headers: {}".format(list(entries_t)))
    logger.debug("\n{}".format(entries_t.head(n=10)))

    ledgers = pd.read_csv(args.ledgers, sep=',')
    logger.info("loaded ledgers {} rows".format(len(ledgers)))
    logger.debug("Headers: {}".format(list(ledgers)))
    logger.debug("\n{}".format(ledgers.head(n=10)))

    apps_t = pd.read_csv(args.apps, sep=',')
    logger.info("loaded apps {} rows".format(len(apps_t)))
    logger.debug("Headers: {}".format(list(apps_t)))
    logger.debug("\n{}".format(apps_t.head(n=10)))

    entries = [Entry(entries_t.iloc[i]) for i in range(len(entries_t))]

    def predict_docs(arena, entry, _id, _type: LType):
        if not _id:
            return ""
        docs = find_best_docs(arena.playground.values(), entry, _id, _type)
        return ";".join([d["entry"].doc_no for d in docs])

    l_entries = [LEntry(ledgers.iloc[i]) for i in range(len(ledgers))]
    apps = [App(apps_t.iloc[i]) for i in range(len(apps_t))]
    arena = Arena(l_entries, apps)

    with open(args.pred, 'r') as f2:
        pred_i = iter(f2)
        with tqdm(desc="predicting", total=len(entries)) as pr_bar:
            for i in range(len(entries)):
                cv_pred = next(pred_i).strip()
                preds = cv_pred.split("\t")
                cust = preds[0].split(":")
                arena.move(entries[i].date)
                pr_bar.update(1)
                res = "{}\t{}\t{}".format(preds[0], predict_docs(arena, entries[i], cust[1], LType.from_s(cust[0])),
                                          preds[2])
                print(res)

    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
