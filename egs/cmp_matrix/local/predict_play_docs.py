import argparse
import sys

from jsonlines import jsonlines
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

    entries_t = []
    with jsonlines.open(args.input) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")
            entries_t.append(d)
    logger.info("loaded entries {} rows".format(len(entries_t)))

    ledgers = []
    with jsonlines.open(args.ledgers) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")
            ledgers.append(d)
    logger.info("loaded ledgers {} rows".format(len(ledgers)))

    apps_t = []
    with jsonlines.open(args.apps) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")
            apps_t.append(d)
    logger.info("loaded apps {} rows".format(len(apps_t)))

    entries = [Entry(e) for e in entries_t]
    l_entries = [LEntry(_l) for _l in ledgers]
    apps = [App(_i) for _i in apps_t]

    def predict_docs(arena, entry, _id, _type: LType):
        if not _id:
            return ""
        docs = find_best_docs(arena.playground.values(), entry, _id, _type)
        return ";".join([d["entry"].doc_no for d in docs])

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
                res = "{}\t{}\t{}\t{}".format(preds[0], predict_docs(arena, entries[i], cust[1], LType.from_s(cust[0])),
                                              preds[2], preds[3] if len(preds) > 3 else "")
                print(res)

    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
