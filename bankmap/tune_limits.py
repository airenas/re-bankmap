import json
import os
import sys
import time
from datetime import datetime, timedelta

from bankmap.cfg import PredictionCfg
from bankmap.data import LEntry, Entry, Ctx, LType, Arena, App, use_e2e
from bankmap.history_stats import Stats
from bankmap.loaders.apps import load_apps
from bankmap.loaders.entries import load_docs_map, load_bank_recognitions_map, load_entries
from bankmap.loaders.ledgers import load_gls, load_ba, load_vendor_sfs, load_customer_sfs
from bankmap.logger import logger
from bankmap.similarity.similarities import similarity, sim_val, prepare_history_map
from bankmap.tune.tune import Cmp, calc_limits
from bankmap.utils.utils import empty_if_n, str_date


def get_best_account(ctx, arena, entry, entry_dict):
    bv, be = -1, None
    dt = entry.date
    arena.move(dt)
    ctx.stats.move(dt)

    def check(e):
        nonlocal bv, be
        v = similarity(ctx, e, entry, entry_dict)
        out = sim_val(ctx, v)
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
    c_docs_map = load_docs_map(os.path.join(data_dir, "customerRecognitions.jsonl"), "Customer")
    v_docs_map = load_docs_map(os.path.join(data_dir, "vendorRecognitions.jsonl"), "Vendor")
    res_info = {"customer_recognitions": len(c_docs_map), "vendor_recognitions": len(v_docs_map)}
    cv_docs_map = c_docs_map
    cv_docs_map.update(v_docs_map)

    ba_map = load_bank_recognitions_map(os.path.join(data_dir, "bankAccountRecognitions.jsonl"))
    res_info["bank_account_recognitions"] = len(ba_map)
    start_t = log_elapsed(start, "load_recognitions")

    entries_df = load_entries(os.path.join(data_dir, "bankStatementEntries.jsonl"), ba_map, cv_docs_map)
    res_info["bank_statement_entries"] = len(entries_df)
    start_t = log_elapsed(start_t, "load_entries")

    customer_sf_df = load_customer_sfs(os.path.join(data_dir, "customerLedgerEntries.jsonl"),
                                       os.path.join(data_dir, "customerBankAccounts.jsonl"),
                                       os.path.join(data_dir, "customers.jsonl"))
    res_info["customer_ledger_entries"] = len(customer_sf_df)

    vendor_sf_df = load_vendor_sfs(os.path.join(data_dir, "vendorLedgerEntries.jsonl"),
                                   os.path.join(data_dir, "vendorBankAccounts.jsonl"),
                                   os.path.join(data_dir, "vendors.jsonl"))
    res_info["vendor_ledger_entries"] = len(vendor_sf_df)
    start_t = log_elapsed(start_t, "load_ledgers")

    gl_df = load_gls(os.path.join(data_dir, "glAccounts.jsonl"))
    res_info["gl_accounts"] = len(gl_df)

    ba_df = load_ba(os.path.join(data_dir, "bankAccounts.jsonl"))
    res_info["bank_accounts"] = len(ba_df)
    start_t = log_elapsed(start_t, "load_gl_ba")

    gl_ba = [LEntry(r) for r in gl_df] + \
            [LEntry(r) for r in ba_df]
    sfs = [LEntry(r) for r in customer_sf_df] + \
          [LEntry(r) for r in vendor_sf_df]
    start_t = log_elapsed(start_t, "prepare_ledgers")

    l_entries = sfs + gl_ba
    customer_apps_df = load_apps(os.path.join(data_dir, "customerApplications.jsonl"), l_entries, "Customer")
    res_info["customer_applications"] = len(customer_apps_df)

    vendor_apps_df = load_apps(os.path.join(data_dir, "vendorApplications.jsonl"), l_entries, "Vendor")
    res_info["vendor_applications"] = len(vendor_apps_df)
    res_info["l_entries"] = len(l_entries)
    start_t = log_elapsed(start_t, "load_applications")

    entries = [Entry(e) for e in entries_df]
    apps = [App(r) for r in customer_apps_df] + \
           [App(r) for r in vendor_apps_df]

    entries = [e for e in entries if e.rec_type != LType.UNSET]
    entries.sort(key=lambda e: e.date.timestamp() if e.date else 1)
    log_elapsed(start_t, "prepare_entries")
    historical_entries = prepare_history_map(entries)
    log_elapsed(start_t, "prepare_entries")
    arena = Arena(l_entries, apps)
    stats = Stats(entries)
    log_elapsed(start_t, "prepare_arena")
    start_t = log_elapsed(start, "prepare_total")

    logger.warning("predicting...")
    test = entries[-min(len(entries), cfg.train_last):]
    logger.info("predicting last {} entries".format(len(test)))
    res_info["tune_count"] = len(test)
    cmps = []
    ctx = Ctx(stats=stats, use_e2e=use_e2e(l_entries))
    logger.info(f"use_e2e {ctx.use_e2e}")
    res_info["use_e2e"] = ctx.use_e2e
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
    return "stats:{}:{}:{}   cfg:{}:{}".format(empty_if_n(cfg.company), param.get("bank_statement_entries"),
                                               param.get("tune_count"), empty_if_n(cfg.tune_count),
                                               str_date(cfg.tune_date))


def add_tune_into_cfg(cfg: PredictionCfg, limits, info):
    cfg.limits = limits
    cfg.tune_count = info.get("tune_count", 0)
    next_days = 7
    if cfg.tune_count < 500:
        next_days = 1
    cfg.next_train = datetime.now() + timedelta(days=next_days)
    cfg.tune_date = datetime.now()
    cfg.version = PredictionCfg.version()
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
