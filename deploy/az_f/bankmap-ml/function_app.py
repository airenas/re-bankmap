import base64
import json
import os
import time
import ulid
from datetime import datetime
from http import HTTPStatus

import azure.functions as func
from azure.functions import HttpMethod

from bankmap.az.config import load_config_or_default
from bankmap.az.zip import copy_data, save_extract_zip, upload_file, get_container_name
from bankmap.cfg import PredictionCfg
from bankmap.logger import logger

# from azure.ai.ml import dsl, Input, Output


class FunctionCfg:
    def __init__(self):
        self.compute_cluster = os.getenv('COMPUTE_CLUSTER', 'cpu-cluster-lp')
        self.input_path_template = os.getenv('INPUT_DATA_PATH_TEMPLATE',
                                             'azureml://subscriptions/ae0eff97-7885-4c1e-b23c-d8a627ef292f/'
                                             'resourcegroups/DocuBank/workspaces/test/datastores/datawork/paths/{}.zip')
        self.config_path = os.getenv('CONFIG_PATH',
                                             'azureml://subscriptions/ae0eff97-7885-4c1e-b23c-d8a627ef292f/'
                                             'resourcegroups/DocuBank/workspaces/test/datastores/configs/paths/')                                             
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
    id = str(ulid.new())

    company = req.headers.get("RecognitionForId", None)
    logger.info("RecognitionForId {}".format(company))
    logger.info(f"ID {id}")
    try:
        if company:
            company = base64.b64decode(company.encode('ascii')).decode('utf-8')
        logger.info("company {}".format(company))
        cfg = load_config_or_default(company)

        # TODO: no need to save to local storage    
        zip_bytes = req.get_body()
        data_dir, out_file, temp_dir = save_extract_zip(zip_bytes)
        
        check_copy_data(cfg, out_file)
        check_copy_work_data(cfg, id, out_file)
        next_t = log_elapsed(start, "copy_to_storage", metrics)

        logger.info("pass to ml pipeline")
        job_id, metrics_pipe = pass_to_ml(id, company)
        metrics.update(metrics_pipe)
        log_elapsed(next_t, "total_start_pipeline", metrics)
        log_elapsed(start, "total", metrics)
        info = {"app_version": app_ver}
        logger.info(json.dumps(info, indent=2))
        logger.info("done mapping")
        res = {"company": company, "id": id, "job_id": job_id, "metrics": metrics, "info": info}
        return json_resp(res, HTTPStatus.OK)
    except BaseException as err:
        logger.exception(err)
        return json_resp({"error": str(err)}, HTTPStatus.INTERNAL_SERVER_ERROR)


def pass_to_ml(id: str, company: str):
    start, metrics = time.time(), {}
    cfg = FunctionCfg()
    ml_client = get_client(cfg)
    next_t = log_elapsed(start, "init_ml_client", metrics)

    logger.info(f"Cluster: {cfg.compute_cluster}")
    input_file = cfg.input_path_template.format(id)
    logger.info(f"Input file: {input_file}")
    logger.info(f"Configs: {cfg.config_path}")
    logger.info(f"ML component: {cfg.ml_component}")

    component = ml_client.components.get(cfg.ml_component)
    logger.info(f'output: {component.outputs}')
    next_t = log_elapsed(next_t, "init_pipeline_component", metrics)

    from azure.ai.ml import dsl, Input, Output
    @dsl.pipeline(compute=cfg.compute_cluster, description=f"Map pipeline for {company}")
    def map_pipeline(company, data, config_path):
        job = component(company=company, data=data, config_path=config_path)
        return {
            "output": job.outputs.output
        }
    pl = map_pipeline(company=company, data=Input(type="uri_file", path=input_file), config_path=Input(type="uri_folder", path=cfg.config_path))
    next_t = log_elapsed(next_t, "init_pipeline", metrics)
    pipeline_job = ml_client.jobs.create_or_update(pl, experiment_name=f"map for {company}")
    logger.info(f'output: {pipeline_job.name}')
    log_elapsed(next_t, "create_job", metrics)
    return pipeline_job.name, metrics


@app.function_name(name="bankmap-status")
@app.route(route="status/{jobID}", methods=[HttpMethod.GET]) 
def map_function(req: func.HttpRequest) -> func.HttpResponse:
    job_id = req.route_params.get('jobID')
    logger.info(f"got request for {job_id}")
    app_ver = get_version()
    logger.info("version {}".format(app_ver))
    try:
        status = get_status(job_id)
        res = {"status": status, "job_id": job_id}
        return json_resp(res, HTTPStatus.OK)
    except BaseException as err:
        logger.exception(err)
        return json_resp({"error": str(err)}, HTTPStatus.INTERNAL_SERVER_ERROR) 


@app.function_name(name="bankmap-result")
@app.route(route="result/{jobID}", methods=[HttpMethod.GET]) 
def map_function(req: func.HttpRequest) -> func.HttpResponse:
    job_id = req.route_params.get('jobID')
    logger.info(f"got resulr request for {job_id}")
    app_ver = get_version()
    logger.info("version {}".format(app_ver))
    try:
        res = get_result(job_id)
        return json_resp(res, HTTPStatus.OK)
    except BaseException as err:
        logger.exception(err)
        return json_resp({"error": str(err)}, HTTPStatus.INTERNAL_SERVER_ERROR)  


def get_client(cfg):
    logger.info(f"Workspace: {cfg.workspace}")
    logger.info(f"Subscription ID: {cfg.subscription_id}")
    
    from azure.identity import DefaultAzureCredential
    credential = DefaultAzureCredential()
    credential.get_token("https://management.azure.com/.default")
    
    from azure.ai.ml import MLClient
    # Get a handle to the workspace
    return MLClient(
        credential=credential,
        subscription_id=cfg.subscription_id,
        resource_group_name="DocuBank",
        workspace_name=cfg.workspace,
    )



def get_status(id: str):
    ml_client = get_client(FunctionCfg())

    retrieved_job = ml_client.jobs.get(id)
    return retrieved_job.status



def get_result(id: str):
    ml_client = get_client(FunctionCfg())
    import tempfile
    temp_dir = tempfile.TemporaryDirectory()
    logger.info("tmp dir {}".format(temp_dir.name))
    ml_client.jobs.download(name=id, download_path=temp_dir.name, output_name="output")
    out_file = os.path.join(temp_dir.name, "named-outputs/output/output")
    logger.info("out_file {}".format(out_file))
    with open(out_file, "rb") as f:
        data = f.read()
    return json.loads(str(data, "utf-8"))
