import argparse
import os
import sys

from azure.ai.ml import MLClient
from azure.ai.ml.entities import AmlCompute, Environment
from azure.identity import DefaultAzureCredential

from bankmap.logger import logger


class Params:
    def __init__(self):
        self.subscription_id = os.getenv("SUBSCRIPTION_ID")
        self.workspace_name = os.getenv("WORKSPACE_NAME")
        self.version = os.getenv("VERSION")
        self.cpu_compute_target = "cpu-cluster-lp"
        self.conda_file = "./conda.yaml"
        self.code_dir = "./src"
        self.env_name = "bankmap"
        self.component_name = "bankmap"
        self.config_path = f"azureml://subscriptions/{self.subscription_id}/resourcegroups/DocuBank/workspaces/{self.workspace_name}/datastores/configs/paths/"
        self.input_path = f"azureml://subscriptions/{self.subscription_id}/resourcegroups/DocuBank/workspaces/{self.workspace_name}/datastores/datawork/paths/"


def init_client(params: Params):
    credential = DefaultAzureCredential()

    ml_client = MLClient(
        credential=credential,
        subscription_id=params.subscription_id,
        resource_group_name="DocuBank",
        workspace_name=params.workspace_name,
    )
    return ml_client


def init_cluster(ml_client, params: Params):
    try:
        cpu_cluster = ml_client.compute.get(params.cpu_compute_target)
        logger.info(f"You already have a cluster named {params.cpu_compute_target}, we'll reuse it as is.")

    except Exception:
        logger.info("Creating a new cpu compute target...")
        cpu_cluster = AmlCompute(name=params.cpu_compute_target,
                                 type="amlcompute",
                                 size="STANDARD_DS3_V2",
                                 min_instances=0,
                                 max_instances=30,
                                 idle_time_before_scale_down=600,
                                 tier="LowPriority",
                                 )
        logger.info(f"AMLCompute with name {cpu_cluster.name} will be created, with compute size {cpu_cluster.size}")
        cpu_cluster = ml_client.compute.begin_create_or_update(cpu_cluster)

    return cpu_cluster


def init_env(ml_client, params: Params):
    pipeline_job_env = Environment(
        name=params.env_name,
        description="Env to run map pipeline",
        tags={"bankmap": params.version},
        conda_file=params.conda_file,
        image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest",
        version=params.version,
    )
    pipeline_job_env = ml_client.environments.create_or_update(pipeline_job_env)
    logger.info(
        f"Environment with name {pipeline_job_env.name} is registered to workspace, the environment version is {pipeline_job_env.version}")
    return pipeline_job_env


def init_component(ml_client, env, params: Params):
    from azure.ai.ml import command
    from azure.ai.ml import Input, Output

    outputs = {"output": Output(type="uri_file", mode="rw_mount")}
    logger.info(f"outputs {outputs}")
    map_component = command(
        name=params.component_name,
        display_name="Maps statement to DB for a company",
        description="Maps statement to DB for a company",
        inputs={
            "data": Input(type="uri_file"),
            "config_path": Input(type="uri_folder"),
            "company": Input(type="string")
        },
        is_deterministic=True,
        outputs=outputs,
        # The source folder of the component
        code=params.code_dir,
        version=params.version,
        command="""python map.py \
            --company '${{inputs.company}}' \
            --input_file '${{inputs.data}}'\
            --config_path '${{inputs.config_path}}'\
            --output '${{outputs.output}}'\
            """,
        environment=f"{env.name}:{env.version}",
    )

    # Now we register the component to the workspace
    map_component = ml_client.create_or_update(map_component.component)

    # Create (register) the component in your workspace
    logger.info(
        f"Component {map_component.name} with Version {map_component.version} is registered"
    )
    return map_component


def test(ml_client, params: Params):
    from azure.ai.ml import dsl, Input

    map_component = ml_client.components.get(params.component_name)
    logger.info(f'output: {map_component}')

    @dsl.pipeline(
        name="map",
        compute=params.cpu_compute_target,
        description="test map pipeline"
    )
    def map_pipeline(company, data, config_path):
        job = map_component(company=company, data=data, config_path=config_path)
        logger.info(f'output: {job.outputs["output"]}')
        return {
            "output": job.outputs.output
        }

    company = "hum"
    pipeline = map_pipeline(
        company=company,
        data=Input(type="uri_file",
                   path=f"azureml://subscriptions/{params.subscription_id}/resourcegroups/DocuBank/workspaces/{params.workspace_name}/datastores/datacopy/paths/{company}.zip"),
        config_path=Input(type="uri_folder", path=params.config_path)
    )

    pipeline_job = ml_client.jobs.create_or_update(pipeline, experiment_name="Test map deploy", )
    logger.info(f'output: {pipeline_job.outputs.output.path}')
    logger.info(f'output: {pipeline_job.name}')


def main(argv):
    parser = argparse.ArgumentParser(description="Deploys map pipeline",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--run", nargs='?', required=True, help="Command: deploy/test")
    args = parser.parse_args(args=argv)
    logger.info("Starting")
    params = Params()
    logger.info(f"version : {params.version}")
    logger.info(f"workspace_name : {params.workspace_name}")
    logger.info(f"subscription_id : {params.subscription_id}")
    logger.info(f"cpu_compute_target : {params.cpu_compute_target}")

    logger.info("Init client")
    client = init_client(params)
    if args.run == "deploy":
        logger.info("Check cluster")
        cluster = init_cluster(client, params)
        logger.info("Check env")
        env = init_env(client, params)
        logger.info("Check component")
        env = init_component(client, env, params)
    if args.run == "test":
        logger.info("Run test")
        test(client, params)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
