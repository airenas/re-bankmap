import json
import os
import tempfile
import time
import zipfile
from http import HTTPStatus

import azure.functions as func
from azure.functions import HttpMethod

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


def get_fake_str():
    with open("fake.json", "r") as f:
        return f.read().strip()


@app.function_name(name="bankmap")
@app.route(route="map", methods=[HttpMethod.POST])  # HTTP Trigger
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    app_ver = get_version()
    logger.info("version {}".format(app_ver))
    logger.info("got request")
    file = req.files.get("file", None)
    if not file:
        return json_resp({"error": "no file"}, HTTPStatus.BAD_REQUEST)
    company = req.form.get("company", None)
    # if not company:
    #     return json_resp({"error": "no company"}, HTTPStatus.BAD_REQUEST)
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

        with zipfile.ZipFile(out_file) as z:
            z.extractall(temp_dir.name)
        logger.info("saved files {}".format(temp_dir.name))

        return func.HttpResponse(body=get_fake_str(), status_code=int(HTTPStatus.OK), mimetype="application/json")
    except BaseException as err:
        logger.error(err)
        return json_resp({"error": str(err)}, HTTPStatus.INTERNAL_SERVER_ERROR)
