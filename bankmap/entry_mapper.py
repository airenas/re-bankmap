import json
import os
import sys
import time

from bankmap.cfg import PredictionCfg
from bankmap.data import LEntry, Entry, LType, Ctx, PredictData
from bankmap.loaders.entries import load_docs_map, load_bank_recognitions_map, load_entries, load_lines
from bankmap.loaders.ledgers import load_gls, load_ba, load_vendor_sfs, load_customer_sfs
from bankmap.logger import logger
from bankmap.predict.docs import find_best_docs
from bankmap.similarity.similarities import similarity, sim_val, prepare_history_map


def to_dic_item(e: LEntry):
    return {"no": e.id, "type": e.type.to_s(), "name": e.name}


def to_dic_sf(e: LEntry):
    return {"no": e.doc_no, "ext_no": e.ext_doc, "type": e.doc_type.to_s(),
            "currency": e.currency, "amount": e.amount, "due": e.due_date.isoformat()}


def to_dic_entry(e: Entry):
    return {"amount": e.amount, "date": e.date.isoformat(), "msg": e.msg,
            "currency": e.currency, "desc": e.who, "id": e.ext_id, "type": e.type.to_s(),
            "bank_account": e.bank_account}


def predict_entry(ctx, pd, entry, cfg):
    logger.info("Recognizing: {}, {}, {}".format(entry.date, entry.amount, entry.ext_id))
    pred = []

    def check(_e):
        v = similarity(ctx, _e, entry, pd.historical_entries)
        out = sim_val(v)
        pred.append({"i": out, "sim": v, "entry": _e})

    for e in pd.gl_ba:
        check(e)
    for e in pd.sfs:
        check(e)

    pred.sort(key=lambda x: sim_val(x["sim"]), reverse=True)
    res = {"entry": to_dic_entry(entry)}
    recognized = None
    was = set()
    if len(pred) > 0:
        e = pred[0]
        recognized = e["entry"]
        res["main"] = {"item": to_dic_item(recognized), "similarity": e["i"], "recommended": bool(e["i"] > cfg.limit)}
        was.add(recognized.id)
    alt = []
    i = 1
    for r in pred:
        if i >= cfg.tops:
            break
        rec = r["entry"]
        if rec.id in was:
            continue
        was.add(rec.id)
        i += 1
        alt.append({"item": to_dic_item(rec), "similarity": r["i"], "recommended": False})
    res["alternatives"] = alt
    if recognized and recognized.type in [LType.VEND, LType.CUST]:
        predicted_docs = find_best_docs(pd.sfs, entry, recognized.id, recognized.type)
        res_docs = []
        total_applied = 0
        for d in predicted_docs:
            res_docs.append({"item": to_dic_sf(d["entry"]), "sum": d["sum"], "reason": d["reason"]})
            total_applied += d["sum"]
        res["main"]["docs"] = res_docs
        res["main"]["total_applied"] = total_applied
        res["main"]["amount_remaining"] = entry.amount - total_applied
    return res


def do_mapping(data_dir, cfg: PredictionCfg):
    metrics = {}

    def log_elapsed(_start, what):
        end = time.time()
        elapsed = (end - _start)
        metrics[what + "_sec"] = elapsed
        return end

    start = time.time()
    logger.info("data dir {}".format(data_dir))
    c_docs_map = load_docs_map(os.path.join(data_dir, "Customer_Recognitions.csv"), "Cust")
    v_docs_map = load_docs_map(os.path.join(data_dir, "Vendor_Recognitions.csv"), "Vend")
    res_info = {"Customer_Recognitions": len(c_docs_map), "Vendor_Recognitions": len(v_docs_map)}
    cv_docs_map = c_docs_map
    cv_docs_map.update(v_docs_map)

    ba_map = load_bank_recognitions_map(os.path.join(data_dir, "Bank_Account_Recognitions.csv"))
    res_info["Bank_Account_Recognitions"] = len(ba_map)
    start_t = log_elapsed(start, "load_recognitions")

    entries_df = load_entries(os.path.join(data_dir, "Bank_Statement_Entries.csv"), ba_map, c_docs_map)
    res_info["Bank_Statement_Entries"] = len(entries_df)
    start_t = log_elapsed(start_t, "load_entries")

    customer_sf_df = load_customer_sfs(os.path.join(data_dir, "Customer_Ledger_Entries.csv"),
                                       os.path.join(data_dir, "Customer_Bank_Accounts.csv"),
                                       os.path.join(data_dir, "Customers.csv"))
    res_info["Customer_Ledger_Entries"] = len(customer_sf_df)

    vendor_sf_df = load_vendor_sfs(os.path.join(data_dir, "Vendor_Ledger_Entries.csv"),
                                   os.path.join(data_dir, "Vendor_Bank_Accounts.csv"),
                                   os.path.join(data_dir, "Vendors.csv"))
    res_info["Vendor_Ledger_Entries"] = len(vendor_sf_df)
    start_t = log_elapsed(start_t, "load_ledgers")

    gl_df = load_gls(os.path.join(data_dir, "GL_Accounts.csv"))
    res_info["GL_Accounts"] = len(gl_df)

    ba_df = load_ba(os.path.join(data_dir, "Bank_Accounts.csv"))
    res_info["Bank_Accounts"] = len(ba_df)
    start_t = log_elapsed(start_t, "load_gl_ba")

    gl_ba = [LEntry(r) for r in gl_df.to_dict('records')] + \
            [LEntry(r) for r in ba_df.to_dict('records')]
    sfs = [LEntry(r) for r in customer_sf_df.to_dict('records')] + \
          [LEntry(r) for r in vendor_sf_df.to_dict('records')]
    start_t = log_elapsed(start_t, "prepare_ledgers")

    sfs = [s for s in sfs if s.open]
    res_info["Open_SFs"] = len(sfs)
    for s in sfs:
        s.amount = s.remaining_amount
    # customer_apps_df = load_customer_apps(os.path.join(data_dir, "Customer_Applications.csv"), l_entries)
    # res_info["Customer_Applications"] = len(customer_apps_df)

    # vendor_apps_df = load_vendor_apps(os.path.join(data_dir, "Vendor_Applications.csv"), l_entries)
    # res_info["Vendor_Applications"] = len(vendor_apps_df)
    # res_info["l_entries"] = len(l_entries)
    # start_t = log_elapsed(start_t, "load_applications")

    new_entries = load_lines(os.path.join(data_dir, "Bank_Statement_Lines.csv"))
    res_info["Bank_Statement_Lines"] = len(new_entries)
    start_t = log_elapsed(start_t, "load_entry_lines")

    entries_d = entries_df.to_dict('records')
    entries = [Entry(e) for e in entries_d]
    # apps = [App(r) for r in customer_apps_df.to_dict('records')] + \
    #        [App(r) for r in vendor_apps_df.to_dict('records')]

    entries.sort(key=lambda e: e.date.timestamp() if e.date else 1)
    log_elapsed(start_t, "prepare_entries")
    pd = PredictData(gl_ba=gl_ba, sfs=sfs, historical_entries=prepare_history_map(entries))
    log_elapsed(start_t, "prepare_entries")
    start_t = log_elapsed(start, "prepare_total")

    logger.warning("predicting...")
    test = new_entries
    predict_res = []
    ctx = Ctx()
    pi = 0
    for entry in test:
        e_res = predict_entry(ctx, pd, entry, cfg)
        predict_res.append(e_res)
        pi += 1
    log_elapsed(start_t, "predicting")
    log_elapsed(start, "total_mapping")
    if pi > 0:
        metrics["predicting_avg_sec"] = (time.time() - start_t) / pi
    return predict_res, {"metrics": metrics, "sizes": res_info}


if __name__ == "__main__":
    res = do_mapping(sys.argv[1], cfg=PredictionCfg())
    print(json.dumps(res[1].get("metrics", {}), indent=2))
    print(json.dumps(res[1].get("sizes", {}), indent=2))
    print(json.dumps(res[0], indent=2))
