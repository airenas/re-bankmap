import os
import argparse
import mlflow

import json
from datetime import datetime

from bankmap.az.zip import save_extract_zip
from bankmap.cfg import PredictionCfg
from bankmap.entry_mapper import do_mapping, make_stats
from bankmap.logger import logger


def load_config(company, path):
    file_name = "{}.json".format(company)
    fp = os.path.join(path, file_name)
    logger.info("load {}".format(fp))
    with open(fp, 'r') as f:
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--company", type=str, required=True, default="")
    parser.add_argument("--input_file", type=str, help="path to input zip file")
    parser.add_argument("--config_path", type=str, help="path to config")
    args = parser.parse_args()

    mlflow.start_run()
    logger.info("company: {}".format(args.company))
    logger.info("input: {}".format(args.input_file))
    logger.info("config_path: {}".format(args.config_path))
    mlflow.set_tag("company", args.company)

    res = process(args.company, args.input_file, args.config_path)
    mlflow.end_run()


def get_version():
    try:
        with open("version.txt", "r") as f:
            return f.read().strip()
    except BaseException as err:
        logger.error(err)
        return "???"


def process(company: str, in_file: str, in_config_path: str):
    app_ver = get_version()
    logger.info("version {}".format(app_ver))
    
    start, metrics = time.time(), {}
    logger.info("got request")

    logger.info("RecognitionForId {}".format(company))
    try:
        logger.info("company {}".format(company))
        cfg = load_config_or_default(company, in_config_path)

        zip_bytes = load_data(in_file)
        mlflow.log_metric("file_size", len(zip_bytes))
        data_dir, out_file, temp_dir = save_extract_zip(zip_bytes)
        next_t = log_elapsed(start, "extract_zip", metrics)

        logger.info("start mapping")
        mappings, info = do_mapping(data_dir, cfg)

        log_elapsed(next_t, "map", metrics)
        log_elapsed(start, "total", metrics)
        info["metrics"].update(metrics)
        info["app_version"] = app_ver
        logger.info(json.dumps(info, indent=2))
        logger.info("done mapping")
        res = {"company": company, "mappings": mappings, "info": info}
        return json_resp(res, HTTPStatus.OK)
    except BaseException as err:
        logger.exception(err)
        return json_resp({"error": str(err)}, HTTPStatus.INTERNAL_SERVER_ERROR)


if __name__ == "__main__":
    main()
