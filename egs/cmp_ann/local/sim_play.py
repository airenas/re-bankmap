import argparse
import sys

import pandas as pd

from bankmap.data import Entry, LEntry, LType, App, Arena, Ctx
from bankmap.logger import logger
from bankmap.predict.docs import find_best_docs
from bankmap.similarity.similarities import similarity, param_names, sim_imp, prepare_history_map
import tensorflow as tf


def show_sim_importance(sim):
    res = []
    params = param_names()
    for i, s in enumerate(sim):
        res.append((params[i], s, sim_imp[i], s * sim_imp[i]))
    res.sort(key=lambda v: -v[3])
    for r in res:
        logger.debug(r)


def main(argv):
    parser = argparse.ArgumentParser(description="Calculates similarity for one item (with playground)",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file of bank entries")
    parser.add_argument("--ledgers", nargs='?', required=True, help="Ledgers file")
    parser.add_argument("--apps", nargs='?', required=True, help="Applications file")
    parser.add_argument("--i", nargs='?', required=True, help="Number of entries file to check")
    parser.add_argument("--top", nargs='?', default=20, type=int, help="Show the top most similar items")
    parser.add_argument("--model", nargs='?', required=True, help="Model")
    parser.add_argument("--history", nargs='?', type=int, required=True, help="History in days to look for")
    args = parser.parse_args(args=argv)

    logger.info("Starting")

    entries_t = pd.read_csv(args.input, sep=',')
    logger.info("loaded entries {} rows".format(len(entries_t)))
    logger.debug("Headers: {}".format(list(entries_t)))
    logger.debug("\n{}".format(entries_t.head(n=10)))
    entries = [Entry(e) for e in entries_t.to_dict('records')]

    ledgers = pd.read_csv(args.ledgers, sep=',')
    logger.info("loaded ledgers {} rows".format(len(ledgers)))
    logger.debug("Headers: {}".format(list(ledgers)))
    logger.debug("\n{}".format(ledgers.head(n=10)))
    l_entries = [LEntry(_l) for _l in ledgers.to_dict('records')]

    apps_t = pd.read_csv(args.apps, sep=',')
    logger.info("loaded apps {} rows".format(len(apps_t)))
    logger.debug("Headers: {}".format(list(apps_t)))
    logger.debug("\n{}".format(apps_t.head(n=10)))
    apps = [App(_a) for _a in apps_t.to_dict('records')]

    arena = Arena(l_entries, apps)

    entries.sort(key=lambda e: e.date.timestamp() if e.date else 1)
    entry_dic = prepare_history_map(entries)
    ctx = Ctx(history_days=args.history)

    row = entries[int(args.i)]
    logger.info("\n\n=============================\nTesting bank entry: \n{}".format(entries_t.iloc[int(args.i)]))
    logger.info("Msg       : {}".format(row.msg))
    logger.info("Wanted    : {}".format(row.doc_ids))
    # logger.info("Ext doc no: {}".format(row.ext_id))
    logger.info("=============================\n\n")
    dt = row.date
    logger.info("Entry date: {}".format(dt))

    logger.info("loading model {}".format(args.model))
    model = tf.keras.models.load_model(args.model)
    model.summary(150)
    m_weights = model.layers[1].get_weights()[0]
    m_biases = model.layers[1].get_weights()[1]
    logger.info("w: {}".format(m_weights))
    logger.info("b: {}".format(m_biases))

    arena.add_cust(row.rec_id)

    arena.move(dt)
    res = []
    tmp_v = []

    def check(_e):
        v = similarity(ctx, _e, row, entry_dic)
        res.append({"i": 0, "sim": v, "entry": _e})
        tmp_v.append(v)

    for e in arena.gl_entries:
        check(e)
    for e in arena.playground.values():
        check(e)
    predictions = model.predict(tf.constant(tmp_v), batch_size=1000)
    for i in range(len(res)):
        res[i]["i"] = predictions[i][0]

    res.sort(key=lambda x: x["i"], reverse=True)
    logger.info("\n\n=============================")
    logger.info("Recognized:")
    i, was = 0, set()
    for r in res:
        if i >= args.top:
            break
        key = r["entry"].type.to_s() + ":" + r["entry"].id
        if key in was:
            continue
        i += 1
        was.add(key)
        logger.info(
            "\t{} ({}): {}, {}".format(i, r["i"], r["entry"].to_str(), r["sim"]))
        show_sim_importance(r["sim"])
    logger.info("=============================\n\n")
    if res[0]["entry"].type in [LType.VEND, LType.CUST]:
        res = find_best_docs(arena.playground.values(), row, res[0]["entry"].id, res[0]["entry"].type)
        logger.info("\n\n=============================")
        logger.info("Docs selected {}:".format(len(res)))
        for r in res[:50]:
            logger.info(
                "\t{} -> {}".format(r["reason"], r["entry"].to_str()))
        sel = [r["entry"].doc_no for r in res]
        sel.sort()
        wanted = row.doc_ids.split(";")
        wanted.sort()
        logger.info("\n\n=============================")
        logger.info("Msg       : {}".format(row.msg))
        logger.info("Wanted    : {}".format(",".join(wanted)))
        logger.info("Selected  : {}".format(",".join(sel)))
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
