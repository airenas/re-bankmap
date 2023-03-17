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
from bankmap.logger import logger

app = func.FunctionApp()


def json_resp(value, code: int):
    return func.HttpResponse(body=json.dumps(value), status_code=int(code), mimetype="application/json")


def log_elapsed(_start, what, metrics):
    end = time.time()
    elapsed = (end - _start)
    metrics[what + "_sec"] = elapsed
    return end


@app.function_name(name="bankmap")
@app.route(route="map", methods=[HttpMethod.POST])  # HTTP Trigger
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    start, metrics = time.time(), {}
    logger.info("got request")
    file = req.files.get("file", None)
    if not file:
        return json_resp({"error": "no file"}, HTTPStatus.BAD_REQUEST)
    company = req.form.get("company", None)
    if not company:
        return json_resp({"error": "no company"}, HTTPStatus.BAD_REQUEST)
    extract_dir = req.form.get("extract_dir", "data")
    logger.info("company {}".format(company))
    logger.info("file {}".format(file.name))
    try:

        temp_dir = tempfile.TemporaryDirectory()
        logger.info("tmp dir {}".format(temp_dir))
        out_file = os.path.join(temp_dir.name, "in.zip")
        logger.info("out_file {}".format(out_file))
        with open(out_file, "wb") as f:
            file.save(f)
        logger.info("saved file {}".format(out_file))
        next_t = log_elapsed(start, "save_zip", metrics)

        with zipfile.ZipFile(out_file) as z:
            z.extractall(temp_dir.name)
        logger.info("saved files {}".format(temp_dir.name))
        next_t = log_elapsed(next_t, "extract_zip", metrics)
        data_dir = os.path.join(temp_dir.name, extract_dir)
        logger.info("start mapping")

        mappings, info = do_mapping(data_dir, PredictionCfg(company=company, top_best=3))

        log_elapsed(next_t, "map", metrics)
        log_elapsed(start, "total", metrics)
        info["metrics"].update(metrics)

        logger.info("done mapping")
        res = {"company": company, "mappings": mappings, "info": info}
        return json_resp(res, HTTPStatus.OK)
    except BaseException as err:
        logger.error(err)
        return json_resp({"error": str(err)}, HTTPStatus.INTERNAL_SERVER_ERROR)
