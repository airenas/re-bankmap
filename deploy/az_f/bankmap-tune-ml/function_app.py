import json
import os
from http import HTTPStatus

import azure.functions as func
from azure.ai.ml import MLClient
from azure.ai.ml import dsl, Input, Output
from azure.identity import DefaultAzureCredential

from bankmap.logger import logger

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


# @app.function_name(name="BlobTrigger")
# @app.blob_trigger(arg_name="zipfile",
#                   path=container + "/{name}.zip",
#                   connection="STORAGE_CONNECTION_STRING")
# def test_function(zipfile: func.InputStream):
#     logger.info(f"Python blob trigger function processed blob {zipfile.name}")
#     try:
#         process(zipfile.name)
#     except BaseException as err:
#         logger.exception(err)

def process(zipfile: str):
    app_ver = get_version()
    logger.info("version {}".format(app_ver))
    logger.info(f"File: {zipfile}")
    name = os.path.basename(zipfile)
    company = os.path.splitext(name)[0]
    logger.info(f"Company: {company}")

    # authenticate
    credential = DefaultAzureCredential()
    credential.get_token("https://management.azure.com/.default")

    # Get a handle to the workspace
    ml_client = MLClient(
        credential=credential,
        subscription_id="ae0eff97-7885-4c1e-b23c-d8a627ef292f",
        resource_group_name="DocuBank",
        workspace_name="test",
    )

    tune_component = ml_client.components.get("bankmap_tune")
    logger.info(f'output: {tune_component.outputs}')

    @dsl.pipeline(compute="cpu-cluster-lp", description="Tune pipeline")
    def pipeline(company):
        output_path = "azureml://subscriptions/ae0eff97-7885-4c1e-b23c-d8a627ef292f/resourcegroups/DocuBank/workspaces/test/datastores/devcopy/paths/"
        tune_job = tune_component(company=company)
        tune_job.outputs["output_path"] = Output(type="uri_folder", mode="rw_mount", path=output_path)
        logger.info(f'output: {tune_job.outputs["output_path"]}')
        return {
            "output_path": tune_job.outputs.output_path
        }

    pl = pipeline(company=company)
    pipeline_job = ml_client.jobs.create_or_update(pl, experiment_name=f"tune params")
    logger.info(f'output: {pipeline_job.name}')
    return pipeline_job.name
