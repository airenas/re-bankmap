import json
import os
import sys
import time

from bankmap.cfg import PredictionCfg
from bankmap.data import LEntry, Entry, Ctx, LType, Arena, App
from bankmap.loaders.apps import load_customer_apps, load_vendor_apps
from bankmap.loaders.entries import load_docs_map, load_bank_recognitions_map, load_entries
from bankmap.loaders.ledgers import load_gls, load_ba, load_vendor_sfs, load_customer_sfs
from bankmap.logger import logger
from bankmap.similarity.similarities import similarity, sim_val, prepare_history_map
from bankmap.tune.tune import Cmp, calc_limits


def get_best_account(ctx, arena, entry, entry_dict):
    bv, be = -1, None
    dt = entry.date
    arena.move(dt)

    def check(e):
        nonlocal bv, be
        v = similarity(ctx, e, entry, entry_dict)
        out = sim_val(v)
        if bv < out:
            bv = out
            be = e

    for e in arena.gl_entries:
        check(e)
    for e in arena.playground.values():
        check(e)

    return be, bv


def make_limits(cmps, bars):
    cmps.sort(key=lambda item: (-item.value, item.correct))

    res = {}

    def calc(s):
        res[s] = calc_limits([c for c in cmps if c.type == s], bars)

    res["all"] = calc_limits(cmps, bars)
    calc(LType.CUST.to_s())
    calc(LType.VEND.to_s())
    calc(LType.GL.to_s())
    calc(LType.BA.to_s())
    return res


def tune_limits(cmps, cfg: PredictionCfg):
    limits = make_limits(cmps, [1, 0.995, 0.99, 0.95, 0.9, 0.5])
    return limits


def get_entries_count(data_dir):
    logger.info("data dir {}".format(data_dir))
    c_docs_map = load_docs_map(os.path.join(data_dir, "Customer_Recognitions.csv"), "Cust")
    v_docs_map = load_docs_map(os.path.join(data_dir, "Vendor_Recognitions.csv"), "Vend")
    cv_docs_map = c_docs_map
    cv_docs_map.update(v_docs_map)

    ba_map = load_bank_recognitions_map(os.path.join(data_dir, "Bank_Account_Recognitions.csv"))
    entries_df = load_entries(os.path.join(data_dir, "Bank_Statement_Entries.csv"), ba_map, cv_docs_map)
    entries_d = entries_df.to_dict('records')
    entries = [Entry(e) for e in entries_d]
    entries = [e for e in entries if e.rec_type != LType.UNSET]
    return len(entries)


def predict_entries(data_dir, cfg: PredictionCfg, _from, _to):
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

    l_entries = sfs + gl_ba
    customer_apps_df = load_customer_apps(os.path.join(data_dir, "Customer_Applications.csv"), l_entries)
    res_info["Customer_Applications"] = len(customer_apps_df)

    vendor_apps_df = load_vendor_apps(os.path.join(data_dir, "Vendor_Applications.csv"), l_entries)
    res_info["Vendor_Applications"] = len(vendor_apps_df)
    res_info["l_entries"] = len(l_entries)
    start_t = log_elapsed(start_t, "load_applications")

    entries_d = entries_df.to_dict('records')
    entries = [Entry(e) for e in entries_d]
    apps = [App(r) for r in customer_apps_df.to_dict('records')] + \
           [App(r) for r in vendor_apps_df.to_dict('records')]

    entries = [e for e in entries if e.rec_type != LType.UNSET]
    # stable sort entries
    se = [v for v in enumerate(entries)]
    se.sort(key=lambda e: (e[1].date.timestamp() if e[1].date else 1, e[0]))
    entries = [e[1] for e in se]

    log_elapsed(start_t, "prepare_entries")
    historical_entries = prepare_history_map(entries)
    log_elapsed(start_t, "prepare_entries")
    arena = Arena(l_entries, apps)
    log_elapsed(start_t, "prepare_arena")
    start_t = log_elapsed(start, "prepare_total")

    logger.warning("predicting...")
    if _to > len(entries):
        raise RuntimeError("wanted the last index is too large: {}, max {}".format(_to, len(entries)))
    test = entries[_from: _to]
    logger.info("predicting last {} entries".format(len(test)))
    res_info["predicting"] = len(test)
    cmps = []
    ctx = Ctx()
    pi, pr = 0, 0
    for i, entry in enumerate(test):
        be, bv = get_best_account(ctx, arena, entry, historical_entries)
        cmp = Cmp(_type=be.type.to_s(), value=bv, correct=entry.rec_type == be.type and entry.rec_id == be.id)
        cmps.append(cmp)
        if (i + 1) % 200 == 0:
            logger.info("done {}".format(i + 1))
    log_elapsed(start_t, "predicting")
    log_elapsed(start, "total_predicting")
    if pi > 0:
        metrics["predicting_avg_sec"] = (time.time() - start_t) / pi
        res_info["recommended_percent"] = pr / pi * 100

    return cmps, {"metrics": metrics, "sizes": res_info}


if __name__ == "__main__":
    count = get_entries_count(sys.argv[1])
    cmps, metrics = predict_entries(sys.argv[1], cfg=PredictionCfg(limit=1.0), _from=max(0, count - 2000), _to=count)
    res = tune_limits(cmps, cfg=PredictionCfg(limit=1.0))
    print(json.dumps(metrics.get("metrics", {}), ensure_ascii=False, indent=2))
    print(json.dumps(metrics.get("sizes", {}), ensure_ascii=False, indent=2))
    print(json.dumps(res, ensure_ascii=False, indent=2))
