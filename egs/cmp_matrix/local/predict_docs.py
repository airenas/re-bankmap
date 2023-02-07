from egs.cmp_matrix.local.data import Entry, LEntry
from egs.cmp_matrix.local.similarities import payment_match
from src.utils.logger import logger
from src.utils.similarity import sf_sim_out


def find_best_docs(arena, row: Entry, id: str):
    def amount(a: LEntry):
        return abs(a.amount)

    available = [x for x in arena.playground.values() if x.id == id and payment_match(x, row) and amount(x) > 0.01 ]
    res = []
    remaining_amount = row.amount

    msg = row.msg.casefold()

    def amount_ok(v):
        return abs(v) <= (remaining_amount + 1)

    def add(a: LEntry, why: str, sf_in_msg):
        nonlocal remaining_amount, msg
        res.append({"s": why, "entry": a})
        remaining_amount -= amount(a)
        logger.debug("rem: %.2f - %s:%s" % (remaining_amount, a.doc_no, a.ext_doc))
        available.remove(a)
        if sf_in_msg:
            msg = msg.replace(sf_in_msg.casefold(), " ", 1)

    if len(available) == 1 and amount_ok(available[0].amount):
        add(available[0], "one && amount", None)

    # by sf amount
    for a in list(available):  # sf number
        if a.ext_doc.casefold() in msg and amount_ok(a.amount):
            add(a, "sf && amount", a.ext_doc)
    # by sf sim && amount
    for a in list(available):  # sf number
        sim, sf_in_msg = sf_sim_out(a.ext_doc, msg)
        if sim > 0 and amount_ok(a.amount):
            add(a, "sf sim && amount", sf_in_msg)
            logger.debug("sim: %.2f - %s vs %s" % (sim, a.ext_doc, sf_in_msg))
    # by date
    for a in list(available):  # sf number
        if amount_ok(a.amount):
            add(a, "amount", None)
    return res
