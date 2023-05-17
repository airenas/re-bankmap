import json
import os
from datetime import datetime, timedelta
from http import HTTPStatus

import azure.functions as func
from azure.functions import HttpMethod

from bankmap.az.config import load_config_or_default, save_config
from bankmap.logger import logger

app = func.FunctionApp()


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


@app.function_name(name="BlobTrigger")
@app.blob_trigger(arg_name="zipfile",
                  path="data-copy/{name}.zip",
                  connection="STORAGE_CONNECTION_STRING")
def test_function(zipfile: func.InputStream):
    logger.info(f"Python blob trigger function processed blob {zipfile.name}")
    try:
        (container, file) = zipfile.name.split("/", 1)
        logger.info(f"Container: {container}")
        logger.info(f"Name: {file}")
        company = os.path.splitext(file)[0]
        logger.info(f"Company: {company}")
        cfg = load_config_or_default(company)
        if cfg.next_train and cfg.next_train > datetime.now():
            logger.warn("Skip tune params, next tune after {}".format(cfg.next_train))
            return
        cfg.next_train = datetime.now() + timedelta(days=7)
        save_config(cfg, company)
    except BaseException as err:
        logger.exception(err)


@app.function_name(name="bankmap-tune")
@app.route(route="tune", methods=[HttpMethod.POST])  # HTTP Trigger
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    app_ver = get_version()
    logger.info("version {}".format(app_ver))
    logger.info("got request")
    try:
        res = {"company": "company"}
        return json_resp(res, HTTPStatus.OK)
    except BaseException as err:
        logger.exception(err)
        return json_resp({"error": str(err)}, HTTPStatus.INTERNAL_SERVER_ERROR)
