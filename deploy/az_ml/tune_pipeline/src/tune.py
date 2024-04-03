import os
import argparse
import mlflow

import json
from datetime import datetime

from bankmap.az.zip import save_extract_zip
from bankmap.cfg import PredictionCfg
from bankmap.logger import logger
from bankmap.tune_limits import tune_limits, make_tune_stats, add_tune_into_cfg


def load_config(company, path):
    file_name = "{}.json".format(company)
    fp = os.path.join(path, file_name)
    logger.info("load {}".format(fp))
    with open(fp, 'rb') as f:
        data = f.read()
    logger.debug("data {}".format(str(data, "utf-8")))
    return PredictionCfg.from_dict(json.loads(str(data, "utf-8")))


def load_data(in_file):
    logger.info("load {}".format(in_file))
    with open(in_file, 'rb') as f:
        data = f.read()
    return data


def load_config_or_default(company, path):
    try:
        res = None
        if company:
            res = load_config(company, path)
        if res:
            logger.info("config loaded {}".format(res))
            res.company = company  # make sure we have company
            return res
    except BaseException as err:
        logger.error("Can't load config for {}, {}".format(company, str(err)))

    logger.warning("using default config")
    return PredictionCfg.default(company)


def save_config(cfg: PredictionCfg, company, path):
    file_name = "{}.json".format(company)
    fp = os.path.join(path, file_name)
    logger.info("saving to {}".format(fp))
    with open(fp, 'w') as fw:
        fw.write(json.dumps(cfg.to_dic(), ensure_ascii=False, indent=2))
    logger.info("Uploaded {}".format(fp))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--company", type=str, required=True, default="")
    parser.add_argument("--input_file", type=str, help="path to input zip file")
    parser.add_argument("--output_path", type=str, help="path to output data")
    args = parser.parse_args()

    mlflow.start_run()
    logger.info("company: {}".format(args.company))
    logger.info("input: {}".format(args.input_file))
    logger.info("output_path: {}".format(args.output_path))
    mlflow.set_tag("company", args.company)

    process(args.company, args.input_file, args.output_path)
    mlflow.end_run()


def get_version():
    try:
        with open("version.txt", "r") as f:
            return f.read().strip()
    except BaseException as err:
        logger.error(err)
        return "???"


def process(company: str, in_file: str, out_container: str):
    app_ver = get_version()
    logger.info("version {}".format(app_ver))

    logger.info(f"File: {in_file}")
    logger.info(f"Container: {out_container}")
    logger.info(f"Company: {company}")
    cfg = load_config_or_default(company, out_container)
    if cfg.next_train and cfg.next_train > datetime.now() \
            and PredictionCfg.version() <= cfg.version:
        logger.warn("Skip tune params, next tune after {}".format(cfg.next_train))
        return
    zip_bytes = load_data(in_file)
    mlflow.log_metric("file_size", len(zip_bytes))
    data_dir, out_file, temp_dir = save_extract_zip(zip_bytes)
    logger.info("saved files to {}".format(data_dir))

    logger.info("start tuning limits")
    limits, info = tune_limits(data_dir, cfg)

    info["app_version"] = app_ver
    logger.info(json.dumps(info, ensure_ascii=False, indent=2))
    logger.info("done tuning")
    mlflow.log_metric("tine_count", info.get("sizes", {}).get("tune_count", 0))

    logger.info(make_tune_stats(cfg, info.get("sizes", {})))
    cfg = add_tune_into_cfg(cfg, limits, info.get("sizes", {}))
    logger.info("next tune on {}".format(cfg.next_train))
    save_config(cfg, company, out_container)


if __name__ == "__main__":
    main()
