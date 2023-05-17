import base64
import json
import os
import tempfile
import time
import zipfile
from datetime import datetime
from http import HTTPStatus

import azure.functions as func
from azure.functions import HttpMethod

from bankmap.az.config import load_config_or_default
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


def copy_data_to_storage(company, out_file):
    container_name = os.getenv('DEBUG_STORAGE_CONTAINER')
    if not container_name:
        logger.warn("No DEBUG_STORAGE_CONTAINER set")
        return
    connect_str = os.getenv('DEBUG_STORAGE_CONNECTION_STRING')
    if not connect_str:
        logger.warn("No DEBUG_STORAGE_CONNECTION_STRING set")
        return
    logger.info("container {}".format(container_name))
    from azure.storage.blob import BlobServiceClient

    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    file_name = "{}.zip".format(company)
    # Create a blob client using the local file name as the name for the blob
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
    with open(file=out_file, mode="rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    logger.info("Uploaded {}/{}".format(container_name, file_name))


def check_copy_data(cfg: PredictionCfg, out_file):
    try:
        if cfg.company:
            if not cfg.next_train or cfg.next_train < datetime.now():
                copy_data_to_storage(cfg.company, out_file)
            else:
                logger.warn("Skip save to storage, next save after {}".format(cfg.next_train))
        else:
            logger.warn("Skip save to storage, no company")
    except BaseException as err:
        logger.exception(err)


@app.function_name(name="bankmap")
@app.route(route="map", methods=[HttpMethod.POST])  # HTTP Trigger
def test_function(req: func.HttpRequest) -> func.HttpResponse:
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
        temp_dir = tempfile.TemporaryDirectory()
        logger.info("tmp dir {}".format(temp_dir.name))
        out_file = os.path.join(temp_dir.name, "in.zip")
        logger.info("out_file {}".format(out_file))
        with open(out_file, "wb") as f:
            f.write(zip_bytes)
        logger.info("saved file {} ({}b)".format(out_file, len(zip_bytes)))
        next_t = log_elapsed(start, "save_zip", metrics)

        data_dir = os.path.join(temp_dir.name, "data")
        with zipfile.ZipFile(out_file) as z:
            z.extractall(data_dir)
        logger.info("saved files to {}".format(data_dir))
        next_t = log_elapsed(next_t, "extract_zip", metrics)

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
