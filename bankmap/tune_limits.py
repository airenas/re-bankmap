import json
import os
import sys
import time
from datetime import datetime, timedelta

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


def tune_limits(data_dir, cfg: PredictionCfg):
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
    entries.sort(key=lambda e: e.date.timestamp() if e.date else 1)
    log_elapsed(start_t, "prepare_entries")
    historical_entries = prepare_history_map(entries)
    log_elapsed(start_t, "prepare_entries")
    arena = Arena(l_entries, apps)
    log_elapsed(start_t, "prepare_arena")
    start_t = log_elapsed(start, "prepare_total")

    logger.warning("predicting...")
    test = entries[-min(len(entries), cfg.train_last):]
    logger.info("predicting last {} entries".format(len(test)))
    res_info["tune_count"] = len(test)
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

    limits = make_limits(cmps, [1, 0.995, 0.99, 0.95, 0.9, 0.5])

    return limits, {"metrics": metrics, "sizes": res_info}


def make_tune_stats(cfg: PredictionCfg, param):
    def ein(v):
        return "" if v is None else v

    return "stats:{}:{}:{}   cfg:{}:{}".format(ein(cfg.company), param.get("Bank_Statement_Entries"),
                                               param.get("tune_count"), ein(cfg.tune_count), ein(cfg.tune_date))


def add_tune_into_cfg(cfg: PredictionCfg, limits, info):
    cfg.limits = limits
    cfg.tune_count = info.get("tune_count", 0)
    next_days = 7
    if cfg.tune_count < 500:
        next_days = 1
    cfg.next_train = datetime.now() + timedelta(days=next_days)
    cfg.tune_date = datetime.now()
    return cfg


if __name__ == "__main__":
    cfg = PredictionCfg()
    limits, info = tune_limits(sys.argv[1], cfg=cfg)
    print(json.dumps(info.get("metrics", {}), ensure_ascii=False, indent=2))
    print(json.dumps(info.get("sizes", {}), ensure_ascii=False, indent=2))
    print(json.dumps(limits, ensure_ascii=False, indent=2))
    print(make_tune_stats(cfg, info.get("sizes", {})))
    cfg = add_tune_into_cfg(cfg, limits, info.get("sizes", {}))
    with open(os.path.join(sys.argv[1], "cfg.json"), "w") as f:
        f.write(json.dumps(cfg.to_dic(), ensure_ascii=False, indent=2))
