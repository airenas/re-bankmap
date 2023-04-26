from bankmap.data import Ctx, LEntry, LType, Entry
from bankmap.similarity.similarities import param_names
from bankmap.similarity.similarities import similarity as sim


def similarity(ctx: Ctx, ledger: LEntry, entry: Entry, prev_entries):
    res = sim(ctx, ledger, entry, prev_entries)
    res.append(1 if ledger.type == LType.GL else 0)
    res.append(1 if ledger.type == LType.BA else 0)
    res.append(1 if ledger.type == LType.VEND else 0)
    res.append(1 if ledger.type == LType.CUST else 0)

    # res.append(1 if entry.bank_account == "MASTERCARD" else 0)
    # res.append(1 if entry.bank_account == "SEBEUR" else 0)
    # res.append(1 if entry.bank_account == "VISA" else 0)
    # res.append(1 if entry.bank_account == "SEBNOK" else 0)
    # res.append(1 if entry.bank_account == "SEBUSD" else 0)

    return res


def params_count():
    return len(param_names()) + 4
