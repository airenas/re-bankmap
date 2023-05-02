import json
import os
import tempfile
import time
import zipfile
from http import HTTPStatus

import azure.functions as func
from azure.functions import HttpMethod

from bankmap.cfg import PredictionCfg
from bankmap.entry_mapper import do_mapping
from bankmap.loaders.entries import get_ibans
from bankmap.logger import logger

app = func.FunctionApp()


def json_resp(value, code: int):
    return func.HttpResponse(body=json.dumps(value), status_code=int(code), mimetype="application/json")


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


def check_copy_data(ibans, out_file):
    try:
        value = os.getenv("DEBUG_COMPANY", "")
        logger.info("DEBUG_COMPANY={}".format(value))
        for iban in ibans:
            if ":" + iban + ":" in value:
                logger.warn("Try copy data to storage")
                copy_data_to_storage(iban, out_file)
                logger.info("copied")
                return
        logger.warn("Skip copy data to storage")
    except BaseException as err:
        logger.exception(err)


@app.function_name(name="bankmap")
@app.route(route="map", methods=[HttpMethod.POST])  # HTTP Trigger
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    app_ver = get_version()
    logger.info("version {}".format(app_ver))
    start, metrics = time.time(), {}
    logger.info("got request")

    company = req.headers.get("company", None)
    logger.info("company {}".format(company))
    try:
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

        ibans = get_ibans(os.path.join(data_dir, "Bank_Statement_Lines.csv"))
        logger.info("IBANs={}".format(ibans))
        check_copy_data(ibans, out_file)
        next_t = log_elapsed(next_t, "copy_to_storage", metrics)
        # return json_resp([], HTTPStatus.OK)
        logger.info("start mapping")
        mappings, info = do_mapping(data_dir, PredictionCfg(company=company, top_best=3))

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
