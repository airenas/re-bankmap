import base64
import json
import os
import time
from datetime import datetime
from http import HTTPStatus

import azure.functions as func
from azure.functions import HttpMethod

from bankmap.az.config import load_config_or_default
from bankmap.az.zip import copy_data, save_extract_zip, upload_file, get_container_name
from bankmap.cfg import PredictionCfg
from bankmap.entry_mapper import do_mapping, make_stats
from bankmap.logger import logger
from ulid import ULID


class FynctionCfg:
    def __init__(self):
        self.compute_cluster = os.getenv('COMPUTE_CLUSTER', 'cpu-cluster-lp')
        self.input_path_template = os.getenv('INPUT_DATA_PATH_TEMPLATE',
                                             'azureml://subscriptions/ae0eff97-7885-4c1e-b23c-d8a627ef292f/'
                                             'resourcegroups/DocuBank/workspaces/test/datastores/devcopy/paths/{}.zip')
        self.subscription_id = os.getenv('SUBSCRIPTION_ID')
        self.workspace = os.getenv('ML_WORKSPACE', "test")
        self.ml_component = os.getenv('ML_COMPONENT', "bankmap")


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
            if force_save() or not cfg.next_train or cfg.next_train < datetime.now() \
                    or PredictionCfg.version() > cfg.version:
                copy_data(cfg.company, out_file)
            else:
                logger.warn("Skip save to storage, next save after {}".format(cfg.next_train))
        else:
            logger.warn("Skip save to storage, no company")
    except BaseException as err:
        logger.exception(err)


def name_with_timestamp(company, now):
    return "{}_{}.zip".format(company, now.replace(microsecond=0).isoformat())


def check_copy_work_data(cfg: PredictionCfg, ulid: str, out_file):
    try:
        file_name = f"{ulid}.zip"
        upload_file(file_name, get_container_name("STORAGE_WORK_CONTAINER"), out_file)
    except BaseException as err:
        logger.exception(err)


@app.function_name(name="bankmap-put")
@app.route(route="map", methods=[HttpMethod.POST])  # HTTP Trigger
def map_function(req: func.HttpRequest) -> func.HttpResponse:
    app_ver = get_version()
    logger.info("version {}".format(app_ver))
    start, metrics = time.time(), {}
    logger.info("got request")
    ulid = ULID()

    company = req.headers.get("RecognitionForId", None)
    logger.info("RecognitionForId {}".format(company))
    logger.info(f"ID {ulid}")
    try:
        if company:
            company = base64.b64decode(company.encode('ascii')).decode('utf-8')
        logger.info("company {}".format(company))
        cfg = load_config_or_default(company)

        zip_bytes = req.get_body()
        data_dir, out_file, temp_dir = save_extract_zip(zip_bytes)
        next_t = log_elapsed(start, "extract_zip", metrics)

        check_copy_data(cfg, out_file)
        check_copy_work_data(cfg, ulid, out_file)
        next_t = log_elapsed(next_t, "copy_to_storage", metrics)

        logger.info("pass to ml pipeline")
        job_id = pass_to_ml(ulid, company)
        
        log_elapsed(next_t, "map", metrics)
        log_elapsed(start, "total", metrics)
        info["app_version"] = app_ver
        logger.info(json.dumps(info, indent=2))
        logger.info("done mapping")
        logger.info(make_stats(cfg, info.get("sizes", {})))
        res = {"company": company, "id": ulid, "job_id": ulid, "metrics": metrics}
        return json_resp(res, HTTPStatus.OK)
    except BaseException as err:
        logger.exception(err)
        return json_resp({"error": str(err)}, HTTPStatus.INTERNAL_SERVER_ERROR)


def pass_to_ml(ulid: str, company: str):
    
    cfg = FynctionCfg()
    logger.info(f"Cluster: {cfg.compute_cluster}")
    input_file = cfg.input_path_template.format(ulid)
    logger.info(f"Input file: {input_file}")
    logger.info(f"Workspace: {cfg.workspace}")
    logger.info(f"Subscription ID: {cfg.subscription_id}")
    logger.info(f"ML component: {cfg.ml_component}")

    # authenticate
    credential = DefaultAzureCredential()
    credential.get_token("https://management.azure.com/.default")

    # Get a handle to the workspace
    ml_client = MLClient(
        credential=credential,
        subscription_id=cfg.subscription_id,
        resource_group_name="DocuBank",
        workspace_name=cfg.workspace,
    )

    component = ml_client.components.get(cfg.ml_component)
    logger.info(f'output: {component.outputs}')

    @dsl.pipeline(compute=cfg.compute_cluster, description=f"Map pipeline for {company}")
    def pipeline(company, data):
        output_path = cfg.output_path
        tune_job = tune_component(company=company, data=data)
        tune_job.outputs["output_path"] = Output(type="uri_folder", mode="rw_mount", path=output_path)
        logger.info(f'output: {tune_job.outputs["output_path"]}')
        return {
            "output_path": tune_job.outputs.output_path
        }

    pl = pipeline(company=company, data=Input(type="uri_file", path=input_file))
    pipeline_job = ml_client.jobs.create_or_update(pl, experiment_name=f"tune params for {company}")
    logger.info(f'output: {pipeline_job.name}')
    return pipeline_job.name