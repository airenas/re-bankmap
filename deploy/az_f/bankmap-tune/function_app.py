import json
import os
from datetime import datetime, timedelta

import azure.durable_functions as df
import azure.functions as func

from bankmap.az.config import load_config_or_default, save_config
from bankmap.az.zip import load_data, save_extract_zip
from bankmap.cfg import PredictionCfg
from bankmap.logger import logger
from bankmap.tune.tune import Cmp
from bankmap.tune_limits import get_entries_count, predict_entries


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


app = df.DFApp()


@app.function_name(name="BlobTrigger")
@app.blob_trigger(arg_name="zipfile",
                  path="data-copy/{name}.zip",
                  connection="STORAGE_CONNECTION_STRING")
@app.durable_client_input(client_name="client")
async def tune_function(zipfile: func.InputStream, client):
    instance_id = await client.start_new("tune_limits", client_input={"blob": zipfile.name})
    logger.info("started {}".format(instance_id))


@app.route(route="invoke/{blobName}")
@app.durable_client_input(client_name="client")
async def http_start(req: func.HttpRequest, client):
    blob_name = req.route_params.get('blobName')
    instance_id = await client.start_new("tune_limits", client_input={"blob": "data-copy/" + blob_name})
    response = client.create_check_status_response(req, instance_id)
    logger.info("started {}".format(instance_id))
    return response


@app.orchestration_trigger(context_name="context")
def tune_limits(context: df.DurableOrchestrationContext):
    in_data = context.get_input()
    logger.info("tune_limits {}".format(in_data))
    zip_file = in_data.get("blob")
    if not zip_file:
        logger.exception("no blob provided")
        return

    logger.info(f"Python blob trigger function processed blob {zip_file}")
    try:
        (container, file) = zip_file.split("/", 1)
        logger.info(f"Container: {container}")
        logger.info(f"Name: {file}")
        company = os.path.splitext(file)[0]
        logger.info(f"Company: {company}")
        cfg: PredictionCfg = load_config_or_default(company)
        if not force_tune() and cfg.next_train and cfg.next_train > datetime.now():
            logger.warn("Skip tune params, next tune after {}".format(cfg.next_train))
            return
        zip_bytes = load_data(company)
        data_dir, out_file, temp_dir = save_extract_zip(zip_bytes)
        logger.info("saved files to {}".format(data_dir))

        logger.info("get statement count")
        count = get_entries_count(data_dir)
        logger.info(f"found {count} entries")
        i, step, max_train = 0, 200, min(cfg.train_last, count)
        logger.info(f"will predict last {max_train} entries")

        tasks = []
        while i < max_train:
            train_to = min(i + step, max_train)
            tasks.append(context.call_activity("tune", {"blob": zip_file, "from": i, "to": train_to}))
            i = train_to
        results = yield context.task_all(tasks)
        res = [Cmp.from_dic(item) for one_res in results for item in one_res]
        logger.info("got {} predictions".format(len(res)))
        limits = tune_limits(res, cfg)

        next_days = 7
        if len(res) < 500:
            next_days = 1
        logger.info("next check after {} days".format(next_days))
        cfg.next_train = datetime.now() + timedelta(days=next_days)
        cfg.limits = limits
        save_config(cfg, company)
    except BaseException as err:
        logger.exception(err)


@app.activity_trigger(input_name="params")
def tune(params):
    logger.info("tune {}".format(params))
    zip_file = params.get("blob")
    if not zip_file:
        logger.exception("no blob provided")
        return
    predict_from = params.get("from", 0)
    predict_to = params.get("to", 0)
    if predict_from >= predict_to:
        logger.exception(f"from >= to, {predict_from}, {predict_to}")
        return
    try:
        (container, file) = zip_file.split("/", 1)
        logger.info(f"Container: {container}")
        logger.info(f"Name: {file}")
        company = os.path.splitext(file)[0]
        logger.info(f"Company: {company}")
        cfg: PredictionCfg = load_config_or_default(company)
        if not force_tune() and cfg.next_train and cfg.next_train > datetime.now():
            logger.warn("Skip tune params, next tune after {}".format(cfg.next_train))
            return
        zip_bytes = load_data(company)
        data_dir, out_file, temp_dir = save_extract_zip(zip_bytes)
        logger.info("saved files to {}".format(data_dir))

        logger.info("predicting")
        res, info = predict_entries(data_dir, cfg, predict_from, predict_to)
        logger.info(json.dumps(info, indent=2))
        logger.info("done predicting {}".format(len(res)))
        return [r.to_dic() for r in res]
    except BaseException as err:
        logger.exception(err)
