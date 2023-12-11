import json
import os
import sys
import time

import numpy

from bankmap.cfg import PredictionCfg
from bankmap.data import LEntry, Entry, LType, Ctx, PredictData, TextToAccount
from bankmap.loaders.entries import load_docs_map, load_bank_recognitions_map, load_entries, load_lines
from bankmap.loaders.ledgers import load_gls, load_ba, load_vendor_sfs, load_customer_sfs
from bankmap.loaders.text_to_account import load_text_to_accounts
from bankmap.logger import logger
from bankmap.predict.docs import find_best_docs
from bankmap.predict.text_to_account import map_text_to_account
from bankmap.similarity.similarities import similarity, sim_val, prepare_history_map
from bankmap.utils.utils import empty_if_n, str_date

text_to_account_type_str = "Text to Account"


def to_dic_item(e: LEntry):
    return {"no": e.id, "type": e.type.to_s(), "name": e.name}


def tta_to_dic_item(e: TextToAccount):
    return {"no": e.account, "type": e.type.to_s(), "name": ""}


def to_dic_sf(e: LEntry):
    return {"no": e.doc_no, "ext_no": e.ext_doc, "type": e.doc_type.to_s(),
            "currency": e.currency, "amount": e.amount, "due": e.due_date.isoformat()}


def to_dic_entry(e: Entry):
    return {"amount": e.amount, "date": e.date.isoformat(), "msg": e.msg,
            "currency": e.currency, "desc": e.who, "id": e.ext_id, "type": e.type.to_s(),
            "bank_account": e.bank_account}


def get_limits(limits, _type):
    if limits:
        return limits.get(_type, None)
    return None


def calc_confidence(v, limits):
    if limits and len(limits) > 0:
        for cs, cv in limits.items():
            if v >= cv:
                return float(cs)
        return 0.5  # 0.5 if not found
    return None


def get_confidence(v, _type, cfg: PredictionCfg):
    res = calc_confidence(v, get_limits(cfg.limits, _type))
    if res:
        return res
    res = calc_confidence(v, get_limits(cfg.limits, "all"))
    if res:
        return res
    if v >= cfg.limit:
        return 0.99
    return 0.5


def add_alternatives(cfg, pred, was):
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
    return alt


def predict_entry(ctx, pd, entry, cfg):
    logger.debug("Recognizing: {}, {}, {}".format(entry.date, entry.amount, entry.ext_id))
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
        cs = get_confidence(e["i"], recognized.type, cfg)
        if not (cs >= 0.995 and e["i"] > cfg.text_map_limit):
            logger.debug("try text to account")
            tta = map_text_to_account(entry, pd.text_to_account_map)
            if tta is not None:
                res["main"] = {"item": tta_to_dic_item(tta), "similarity": cfg.text_map_limit, "recommended": True,
                               "confidence_score": 0.995, "type": text_to_account_type_str}
                was.add(tta.account)
                recognized = None
        if "main" not in res:
            res["main"] = {"item": to_dic_item(recognized), "similarity": e["i"], "recommended": cs >= 0.95,
                           "confidence_score": cs, "type": "Similarity"}
            was.add(recognized.id)
            logger.debug("best value: {:.3f}, recommended: {}, type: {}".format(e["i"], bool(e["i"] > cfg.limit),
                                                                                recognized.type.to_s()))

    res["alternatives"] = add_alternatives(cfg, pred, was)
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

    entries_df = load_entries(os.path.join(data_dir, "Bank_Statement_Entries.csv"), ba_map, cv_docs_map)
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

    try:
        text_to_account_map = load_text_to_accounts(os.path.join(data_dir, "Text_to_Account_Mappings.csv"))
    except BaseException as _err:
        logger.error(_err)
        text_to_account_map = []
    res_info["Text_to_Account_Mappings"] = len(text_to_account_map)

    entries.sort(key=lambda e: e.date.timestamp() if e.date else 1)
    log_elapsed(start_t, "prepare_entries")
    pd = PredictData(gl_ba=gl_ba, sfs=sfs, historical_entries=prepare_history_map(entries),
                     text_to_account_map=text_to_account_map)
    log_elapsed(start_t, "prepare_entries")
    start_t = log_elapsed(start, "prepare_total")

    logger.warning("predicting...")
    test = new_entries
    predict_res = []
    ctx = Ctx()
    pi, pr, pr_tta, sims = 0, 0, 0, []
    for entry in test:
        e_res = predict_entry(ctx, pd, entry, cfg)
        main_pred = e_res.get("main")
        if e_res and main_pred:
            pr += 1 if main_pred.get("recommended") else 0
            pr_tta += 1 if main_pred.get("type") == text_to_account_type_str else 0
            sims.append(main_pred.get("similarity", 0))
        predict_res.append(e_res)
        pi += 1
    res_info["recommended"] = pr
    res_info["recommended_tta"] = pr_tta
    log_elapsed(start_t, "predicting")
    log_elapsed(start, "total_mapping")
    if pi > 0:
        metrics["predicting_avg_sec"] = (time.time() - start_t) / pi
        res_info["recommended_percent"] = pr / pi * 100
    if len(sims) > 0:
        for i in [25, 50, 75, 90, 95, 99, 100]:
            res_info["similarity_percentile_{}".format(i)] = numpy.percentile(sims, i)

    return predict_res, {"metrics": metrics, "sizes": res_info}


def make_stats(cfg: PredictionCfg, param):
    return "stats:{}:{}:{}:{}:{}:{}   cfg:{}:{}".format(empty_if_n(cfg.company),
                                                        param.get("Bank_Statement_Entries"),
                                                        param.get("Bank_Statement_Lines"),
                                                        param.get("recommended"), param.get("recommended_tta"),
                                                        int(param.get("recommended_percent", 0)),
                                                        empty_if_n(cfg.tune_count), str_date(cfg.tune_date))


if __name__ == "__main__":
    cfg_loaded = False
    try:
        with open(os.path.join(sys.argv[1], "cfg.json"), "r") as f:
            dic = json.load(f)
            cfg = PredictionCfg.from_dict(dic)
        cfg_loaded = True
    except BaseException as err:
        print(err)
        cfg = PredictionCfg()
    mappings, info = do_mapping(sys.argv[1], cfg=cfg)
    print(json.dumps(info.get("metrics", {}), ensure_ascii=False, indent=2))
    print(json.dumps(info.get("sizes", {}), ensure_ascii=False, indent=2))
    print(make_stats(cfg, info.get("sizes", {})))
    if os.getenv("LOG_LEVEL") == "debug":
        print(json.dumps(mappings, ensure_ascii=False, indent=2))
