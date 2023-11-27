import json
import os
from http import HTTPStatus
from datetime import datetime

import azure.functions as func
from azure.ai.ml import MLClient
from azure.ai.ml import dsl, Input, Output
from azure.identity import DefaultAzureCredential
from bankmap.az.config import load_config_or_default
from bankmap.cfg import PredictionCfg

from bankmap.logger import logger


class FunctionCfg:
    def __init__(self):
        self.compute_cluster = os.getenv('COMPUTE_CLUSTER', 'cpu-cluster-lp')
        self.output_path = os.getenv('OUTPUT_DATA_PATH',
                                     'azureml://subscriptions/ae0eff97-7885-4c1e-b23c-d8a627ef292f/'
                                     'resourcegroups/DocuBank/workspaces/test/datastores/configs/paths/')
        self.input_path_template = os.getenv('INPUT_DATA_PATH_TEMPLATE',
                                             'azureml://subscriptions/ae0eff97-7885-4c1e-b23c-d8a627ef292f/'
                                             'resourcegroups/DocuBank/workspaces/test/datastores/devcopy/paths/{}.zip')
        self.subscription_id = os.getenv('SUBSCRIPTION_ID')
        self.workspace = os.getenv('ML_WORKSPACE', "test")
        self.ml_component = os.getenv('ML_COMPONENT', "bankmap_tune")


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
        p_name = process(container + "/" + blob_name)
        res = {"job_name": p_name}
        return func.HttpResponse(body=json.dumps(res, ensure_ascii=False), status_code=int(HTTPStatus.OK),
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
    logger.info(f"File: {zipfile}")
    name = os.path.basename(zipfile)
    company = os.path.splitext(name)[0]
    logger.info(f"Company: {company}")
    cfg = load_config_or_default(company)
    if not force_tune() and cfg.next_train and cfg.next_train > datetime.now() \
            and PredictionCfg.version() <= cfg.version:
        logger.warn("Skip tune params, next tune after {}".format(cfg.next_train))
        return
    f_cfg = FunctionCfg()
    logger.info(f"Cluster: {f_cfg.compute_cluster}")
    input_file = f_cfg.input_path_template.format(company)
    logger.info(f"Input file: {input_file}")
    logger.info(f"Workspace: {f_cfg.workspace}")
    logger.info(f"Subscription ID: {f_cfg.subscription_id}")
    logger.info(f"ML component: {f_cfg.ml_component}")

    # authenticate
    credential = DefaultAzureCredential()
    credential.get_token("https://management.azure.com/.default")

    # Get a handle to the workspace
    ml_client = MLClient(
        credential=credential,
        subscription_id=f_cfg.subscription_id,
        resource_group_name="DocuBank",
        workspace_name=f_cfg.workspace,
    )

    tune_component = ml_client.components.get(f_cfg.ml_component)
    logger.info(f'output: {tune_component.outputs}')

    @dsl.pipeline(compute=f_cfg.compute_cluster, description=f"Tune pipeline for {company}")
    def pipeline(company, data):
        output_path = f_cfg.output_path
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
