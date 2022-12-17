from egs.cmp_matrix.local.data import Entry, LEntry
from egs.cmp_matrix.local.similarities import payment_match
from src.utils.logger import logger
from src.utils.similarity import sf_sim


def find_best_docs(arena, row: Entry, cust: LEntry):
    available = [x for x in arena.playground.values() if x.id == cust.id and payment_match(x, row)]
    res = []
    remaining_amount = row.amount

    def amount(a: LEntry):
        return abs(a.amount)

    def amount_ok(v):
        return abs(v) <= (remaining_amount + 1)

    def add(a: LEntry, why: str):
        nonlocal remaining_amount
        res.append({"s": why, "entry": a})
        remaining_amount -= amount(a)
        logger.info("rem: %.2f - %s" % (remaining_amount, a.doc_no))
        available.remove(a)

    if len(available) == 1 and amount_ok(available[0].amount):
        add(available[0], "one && amount")

    # by sf amount
    for a in list(available):  # sf number
        if a.ext_doc in row.msg and amount_ok(a.amount):
            add(a, "sf && amount")
    # by sf sim && amount
    for a in list(available):  # sf number
        if sf_sim(a.ext_doc, row.msg) > 0 and amount_ok(a.amount):
            add(a, "sf sim && amount")
    # by date
    for a in list(available):  # sf number
        if amount_ok(a.amount):
            add(a, "amount")
    return res
