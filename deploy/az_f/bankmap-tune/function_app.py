import json
import os
from datetime import datetime, timedelta

import azure.functions as func

from bankmap.az.config import load_config_or_default, save_config
from bankmap.az.zip import load_data, save_extract_zip
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


def force_tune():
    v = os.getenv('FORCE_TUNE', default="").lower()
    return v == "1" or v == "true"


@app.function_name(name="BlobTrigger")
@app.blob_trigger(arg_name="zipfile",
                  path="data-copy/{name}.zip",
                  connection="STORAGE_CONNECTION_STRING")
def test_function(zipfile: func.InputStream):
    app_ver = get_version()
    logger.info("version {}".format(app_ver))
    logger.info(f"Python blob trigger function processed blob {zipfile.name}")
    try:
        (container, file) = zipfile.name.split("/", 1)
        logger.info(f"Container: {container}")
        logger.info(f"Name: {file}")
        company = os.path.splitext(file)[0]
        logger.info(f"Company: {company}")
        cfg = load_config_or_default(company)
        if not force_tune() and cfg.next_train and cfg.next_train > datetime.now():
            logger.warn("Skip tune params, next tune after {}".format(cfg.next_train))
            return
        zip_bytes = load_data(company)
        data_dir, out_file, temp_dir = save_extract_zip(zip_bytes)
        logger.info("saved files to {}".format(data_dir))

        cfg.next_train = datetime.now() + timedelta(days=7)
        save_config(cfg, company)
    except BaseException as err:
        logger.exception(err)
