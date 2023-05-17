import base64
import json
import os
import time
from datetime import datetime
from http import HTTPStatus

import azure.functions as func
from azure.functions import HttpMethod

from bankmap.az.config import load_config_or_default
from bankmap.az.zip import copy_data, save_extract_zip
from bankmap.cfg import PredictionCfg
from bankmap.entry_mapper import do_mapping
from bankmap.logger import logger

app = func.FunctionApp()


def json_resp(value, code: int):
    return func.HttpResponse(body=json.dumps(value, ensure_ascii=False), status_code=int(code),
                             mimetype="application/json")


def log_elapsed(_start, what, metrics):
    end = time.time()
    elapsed = (end - _start)
    metrics[what + "_sec"] = elapsed
    return end


def get_version():
    try:
        with open(".version", "r") as f:
            return f.read().strip()
    except BaseException as err:
        logger.error(err)
        return "???"


def force_save():
    v = os.getenv('FORCE_SAVE', default="").lower()
    return v == "1" or v == "true"


def check_copy_data(cfg: PredictionCfg, out_file):
    try:
        if cfg.company:
            if force_save() or not cfg.next_train or cfg.next_train < datetime.now():
                copy_data(cfg.company, out_file)
            else:
                logger.warn("Skip save to storage, next save after {}".format(cfg.next_train))
        else:
            logger.warn("Skip save to storage, no company")
    except BaseException as err:
        logger.exception(err)


@app.function_name(name="bankmap")
@app.route(route="map", methods=[HttpMethod.POST])  # HTTP Trigger
def map_function(req: func.HttpRequest) -> func.HttpResponse:
    app_ver = get_version()
    logger.info("version {}".format(app_ver))
    start, metrics = time.time(), {}
    logger.info("got request")

    company = req.headers.get("RecognitionForId", None)
    logger.info("RecognitionForId {}".format(company))
    try:
        if company:
            company = base64.b64decode(company.encode('ascii')).decode('utf-8')
        logger.info("company {}".format(company))
        cfg = load_config_or_default(company)

        zip_bytes = req.get_body()
        data_dir, out_file, temp_dir = save_extract_zip(zip_bytes)
        next_t = log_elapsed(start, "extract_zip", metrics)

        check_copy_data(cfg, out_file)
        next_t = log_elapsed(next_t, "copy_to_storage", metrics)

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
