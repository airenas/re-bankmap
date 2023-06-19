import json
import os
from datetime import datetime
from http import HTTPStatus

import azure.functions as func

from bankmap.az.config import load_config_or_default, save_config
from bankmap.az.zip import load_data, save_extract_zip
from bankmap.cfg import PredictionCfg
from bankmap.logger import logger
from bankmap.tune_limits import tune_limits, make_tune_stats, add_tune_into_cfg

app = func.FunctionApp()
container = "data-copy"


def json_resp(value, code: int):
    return func.HttpResponse(body=json.dumps(value, ensure_ascii=False), status_code=int(code),
                             mimetype="application/json")


def get_version():
    try:
        with open(".version", "r") as f:
            return f.read().strip()
    except BaseException as err:
        logger.error(err)
        return "???"


def force_tune():
    v = os.getenv('FORCE_TUNE', default="").lower()
    return v == "1" or v == "true"


@app.function_name(name="HTTPTrigger")
@app.route(route="tune/{blobName}")
def http_start(req: func.HttpRequest):
    blob_name = req.route_params.get('blobName')
    logger.info(f"Python blob trigger function processed blob {blob_name}")
    try:
        process(container + "/" + blob_name)
        return func.HttpResponse(body=json.dumps("done", ensure_ascii=False), status_code=int(HTTPStatus.OK),
                                 mimetype="application/json")
    except BaseException as err:
        logger.exception(err)
        return func.HttpResponse(body=json.dumps(str(err), ensure_ascii=False),
                                 status_code=int(HTTPStatus.INTERNAL_SERVER_ERROROK),
                                 mimetype="application/json")


@app.function_name(name="BlobTrigger")
@app.blob_trigger(arg_name="zipfile",
                  path=container + "/{name}.zip",
                  connection="STORAGE_CONNECTION_STRING")
def test_function(zipfile: func.InputStream):
    logger.info(f"Python blob trigger function processed blob {zipfile.name}")
    try:
        process(zipfile.name)
    except BaseException as err:
        logger.exception(err)


def process(zipfile: str):
    app_ver = get_version()
    logger.info("version {}".format(app_ver))

    (container, file) = zipfile.split("/", 1)
    logger.info(f"Container: {container}")
    logger.info(f"Name: {file}")
    company = os.path.splitext(file)[0]
    logger.info(f"Company: {company}")
    cfg = load_config_or_default(company)
    if not force_tune() and cfg.next_train and cfg.next_train > datetime.now() \
            and PredictionCfg.version() <= cfg.version:
        logger.warn("Skip tune params, next tune after {}".format(cfg.next_train))
        return
    zip_bytes = load_data(company)
    data_dir, out_file, temp_dir = save_extract_zip(zip_bytes)
    logger.info("saved files to {}".format(data_dir))

    logger.info("start tuning limits")
    limits, info = tune_limits(data_dir, cfg)

    info["app_version"] = app_ver
    logger.info(json.dumps(info, indent=2))
    logger.info("done tuning")

    logger.info(make_tune_stats(cfg, info.get("sizes", {})))
    cfg = add_tune_into_cfg(cfg, limits, info.get("sizes", {}))
    logger.info("next tune on {}".format(cfg.next_train))
    save_config(cfg, company)
