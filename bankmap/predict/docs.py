from typing import List

from bankmap.data import LEntry, Entry, LType
from bankmap.logger import logger
from bankmap.similarity.similarities import payment_match
from bankmap.similarity.similarity import sf_sim_out

# flake8: noqa: C901
def find_best_docs(sfs: List[LEntry], row: Entry, _id: str, _type: LType):
    def amount(_a: LEntry):
        return abs(_a.amount)

    available = [x for x in sfs if
                 x.id == _id and x.type == _type and payment_match(x, row) and amount(x) > 0.01]
    res = []
    remaining_amount = row.amount

    msg = row.msg.casefold()

    def amount_ok(v):
        if remaining_amount < 0.01:
            return False
        av = abs(v)
        if av > 10 and remaining_amount > 10:  # allow some deficit
            return av <= (remaining_amount + 1)
        return av <= (remaining_amount + 0.01)

    def add(_a: LEntry, why: str, _sf_in_msg):
        nonlocal remaining_amount, msg
        res.append({"reason": why, "entry": _a, "sum": min(remaining_amount, amount(_a))})
        remaining_amount -= amount(_a)
        logger.debug("rem: %.2f - %s:%s" % (remaining_amount, _a.doc_no, _a.ext_doc))
        available.remove(_a)
        if _sf_in_msg:
            msg = msg.replace(_sf_in_msg.casefold(), " ", 1)

    if len(available) == 1 and amount_ok(available[0].amount):
        add(available[0], "one && amount", None)

    # by sf amount
    for a in list(available):  # sf number
        if a.ext_doc.casefold() in msg and amount_ok(a.amount):
            add(a, "sf && amount", a.ext_doc)
    # by sf
    for a in list(available):  # sf number
        if a.ext_doc.casefold() in msg and remaining_amount > 0:
            add(a, "sf", a.ext_doc)

    def sim_sort_key(e):
        _sim, _ = sf_sim_out(e.ext_doc, msg)
        return -_sim

    available.sort(key=sim_sort_key)
    # by sf sim && amount
    for a in list(available):  # sf number
        sim, sf_in_msg = sf_sim_out(a.ext_doc, msg)
        if sim > 0 and amount_ok(a.amount):
            add(a, "sf sim && amount", sf_in_msg)
            logger.debug("sim: %.2f - %s vs %s" % (sim, a.ext_doc, sf_in_msg))
    # by sf sim
    for a in list(available):  # sf number
        sim, sf_in_msg = sf_sim_out(a.ext_doc, msg)
        if sim > 0 and remaining_amount > 0.005:
            add(a, "sf sim", sf_in_msg)
            logger.debug("sim: %.2f - %s vs %s" % (sim, a.ext_doc, sf_in_msg))

    # by due date
    def sort_due_key(e: LEntry):
        _key = (row.date - e.due_date).total_seconds()
        if _key < 0:  # add minimal preference to on time payment
            _key = abs(_key) + 1
        return _key

    available.sort(key=sort_due_key)
    for a in list(available):  # amount
        if amount_ok(a.amount):
            add(a, "amount", None)
    return res
