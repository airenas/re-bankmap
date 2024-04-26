from typing import List

import numpy as np

from bankmap.data import PaymentType, LEntry, Entry, LType, DocType, Ctx
from bankmap.history_stats import stat_target_key
from bankmap.similarity.similarity import num_sim, date_sim, name_sim, sf_sim


def e_key(e: Entry):
    return e.who.casefold() + e.iban.casefold() + e.bank_account.casefold()


def prepare_history_map(entries: List[Entry]):
    res = {}
    for e in entries:
        res.setdefault(e_key(e), {}).setdefault(e.rec_id, []).append(e)
    return res


def has_past_transaction(ctx: Ctx, e_id, prev_entries, entry):
    max_hist_date = entry.date - ctx.history if ctx.history is not None else None

    for pe in prev_entries.get(e_key(entry), {}).get(e_id, []):
        if max_hist_date and pe.date < max_hist_date:
            continue
        if entry.date <= pe.date:
            return 0
        # logger.info("Found prev {} {} < {}".format(e_key(entry), pe.date, entry.date))
        return 1
    return 0


def payment_match(ledger: LEntry, entry: Entry):
    if entry.type == PaymentType.CRDT and ledger.type == LType.CUST and ledger.doc_type == DocType.SF:
        return True
    if entry.type == PaymentType.DBIT and ledger.type == LType.VEND and ledger.doc_type == DocType.SF:
        return True
    if entry.type == PaymentType.DBIT and ledger.type == LType.CUST and ledger.doc_type == DocType.GRAZ_PAZ:
        return True
    if entry.type == PaymentType.CRDT and ledger.type == LType.VEND and ledger.doc_type == DocType.GRAZ_PAZ:
        return True

    if ledger.type == LType.BA or ledger.type == LType.GL:
        return True
    return False


def amount_match(ledger, entry):
    if ledger.type == LType.BA or ledger.type == LType.GL:
        return 0.5

    diff = entry.amount - ledger.amount
    if not payment_match(ledger, entry):
        diff = entry.amount + ledger.amount
    return num_sim(diff)


def cached_name_sim(ctx, nl, ne):
    res_d = ctx.name_sim_cache.setdefault(nl, {})
    res = res_d.setdefault(ne, None)
    if not res:
        res = name_sim(nl, ne)
        res_d[ne] = res
    # else:
    #     logger.info("found {} {} {}".format(nl, ne, res))
    return res


def iban_sim(l_ibans, e_iban):
    for iban in l_ibans:
        if len(iban) > 5 and iban == e_iban.casefold():
            return 1
    return 0


def similarity(ctx: Ctx, ledger: LEntry, entry, prev_entries):
    res = []
    nl = ledger.name
    ne = entry.who
    res.append(1 if len(ne) > 0 and nl.casefold() == ne.casefold() else 0)
    res.append(cached_name_sim(ctx, nl, ne))
    res.append(iban_sim(ledger.iban, entry.iban))
    res.append(1 if len(ledger.ext_doc) > 5 and ledger.ext_doc.casefold() in entry.msg.casefold() else 0)
    res.append(sf_sim(ledger.ext_doc, entry.msg) if len(ledger.ext_doc) > 5 else 0)
    res.append(date_sim(ledger.due_date, entry.date))
    res.append(date_sim(entry.date, ledger.doc_date))
    res.append(amount_match(ledger, entry))
    # res.append(has_past_transaction(ctx, ledger.id, prev_entries, entry))
    res.append(1 if ledger.currency.casefold() == entry.currency.casefold() else 0)
    res.append(1 if payment_match(ledger, entry) else 0)
    res.append(ctx.stats.who.prob(entry, stat_target_key(ledger.type.to_s(), ledger.id)))
    res.append(ctx.stats.iban.prob(entry, stat_target_key(ledger.type.to_s(), ledger.id)))
    res.append(ctx.stats.iban_msgc.prob(entry, stat_target_key(ledger.type.to_s(), ledger.id)))
    res.append(ctx.stats.who_msgc.prob(entry, stat_target_key(ledger.type.to_s(), ledger.id)))

    if ctx.use_e2e:
        res.append(1 if len(ledger.e2e_id) > 5 and ledger.e2e_id.casefold() == entry.e2e_id.casefold() else 0)

    return res


def param_names(ctx: Ctx):
    if ctx.use_e2e:
        return ["name_eq", "name_sim", "iban_match", "ext_doc", "ext_doc_sim",
                "due_date", "entry_date", "amount_match", "curr_match",
                "payment_match", "who_prob", "iban_prob", "iban_msgc_prob", "who_msgc_prob",
                "e2e_id"]
    return ["name_eq", "name_sim", "iban_match", "ext_doc", "ext_doc_sim",
            "due_date", "entry_date", "amount_match", "curr_match",
            "payment_match", "who_prob", "iban_prob", "iban_msgc_prob", "who_msgc_prob"]


def sim_val(ctx: Ctx, v):
    return np.dot(np.array(v), ctx.sim_weights)


def to_str(param):
    return "{}:{} - {} - {}".format(param["Type"], param["No"], param["Name"], param["Due_Date"])
