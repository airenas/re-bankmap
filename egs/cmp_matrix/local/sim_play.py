import argparse
import sys

from jsonlines import jsonlines

from bankmap.data import Entry, LEntry, LType, App, Arena, Ctx
from bankmap.history_stats import Stats
from bankmap.logger import logger
from bankmap.predict.docs import find_best_docs
from bankmap.similarity.sim_weights import sim_imp
from bankmap.similarity.similarities import sim_val, similarity, param_names, prepare_history_map


def show_sim_importance(ctx, sim):
    res = []
    params = param_names(ctx)
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
    parser.add_argument("--i", nargs='?', required=True, type=int, help="Number of entries file to check")
    parser.add_argument("--top", nargs='?', default=20, type=int, help="Show the top most similar items")
    parser.add_argument("--history", nargs='?', type=int, required=True, help="History in days to look for")
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

    arena = Arena(l_entries, apps)

    entries.sort(key=lambda e: e.date.timestamp() if e.date else 1)
    entry_dic = prepare_history_map(entries)
    stats = Stats(entries)
    ctx = Ctx(history_days=args.history, stats=stats)

    row = entries[args.i]
    stats.move(row.date)
    logger.info("\n\n=============================\nTesting bank entry: \n{}".format(entries_t[args.i]))
    logger.info("Msg       : {}".format(row.msg))
    logger.info("Wanted    : {}".format(row.doc_ids))
    # logger.info("Ext doc no: {}".format(row.ext_id))
    logger.info("=============================\n\n")
    dt = row.date
    logger.info("Entry date: {}".format(dt))

    arena.add_cust(row.rec_id)

    arena.move(dt)
    res = []

    def check(_e):
        v = similarity(ctx, _e, row, entry_dic)
        out = sim_val(ctx, v)
        res.append({"i": out, "sim": v, "entry": _e})

    for e in arena.gl_entries:
        check(e)
    for e in arena.playground.values():
        check(e)

    res.sort(key=lambda x: sim_val(ctx, x["sim"]), reverse=True)
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
            "\t{} ({}): {}, {} - {}".format(i, r["i"], r["entry"].to_str(), r["sim"], sim_val(ctx, r["sim"])))
        show_sim_importance(ctx, r["sim"])
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
