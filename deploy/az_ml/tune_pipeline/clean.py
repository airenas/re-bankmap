import argparse
import os
import sys
from datetime import datetime, timezone, timedelta

from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from mlflow.entities import ViewType
from rich.progress import Progress

from bankmap.logger import logger


class Params:
    def __init__(self):
        self.subscription_id = os.getenv("SUBSCRIPTION_ID")
        self.workspace_name = os.getenv("WORKSPACE_NAME")
        self.version = os.getenv("VERSION")
        self.cpu_compute_target = "cpu-cluster-tune-lp"
        self.conda_file = "./conda.yaml"
        self.code_dir = "./src"
        self.env_name = "bankmap-tune"
        self.component_name = "bankmap_tune"
        self.output_path = f"azureml://subscriptions/{self.subscription_id}/resourcegroups/DocuBank/workspaces/{self.workspace_name}/datastores/configs/paths/"
        self.input_path = f"azureml://subscriptions/{self.subscription_id}/resourcegroups/DocuBank/workspaces/{self.workspace_name}/datastores/datacopy/paths/"


def init_client(params: Params):
    credential = DefaultAzureCredential()

    ml_client = MLClient(
        credential=credential,
        subscription_id=params.subscription_id,
        resource_group_name="DocuBank",
        workspace_name=params.workspace_name,
    )
    return ml_client


def is_ok(run, to_date):
    r_date = datetime.fromtimestamp(run.info.start_time / 1000, tz=timezone.utc)
    return r_date < to_date and run.info.lifecycle_stage != "deleted"


def delete_runs(mlflow, to_date):
    logger.info(f"deleting to {to_date}")
    logger.info(f"loading runs....")
    runs = mlflow.search_runs(experiment_ids=[], max_results=5000, order_by=["start_time ASC"],
                              output_format="list", run_view_type=ViewType.ACTIVE_ONLY,
                              search_all_experiments=True)
    logger.info(f"runs {len(runs)}")
    count = 0
    for r in runs:
        if is_ok(r, to_date):
            count += 1

    logger.info(f"deleting {count}")

    with Progress() as progress:
        task1 = progress.add_task("Deleting runs...", total=count)
        for j, r in enumerate(runs):
            r_date = datetime.fromtimestamp(r.info.start_time / 1000, tz=timezone.utc)
            r_name = r.data.tags.get('mlflow.note.content', r.data.tags.get('company', '??'))
            if is_ok(r, to_date):
                logger.info(f"{j} delete {r_date} {r_name} {r.info.run_id}")
                mlflow.delete_run(r.info.run_id)
                progress.update(task1, advance=1)


def all_deleted(runs):
    for r in runs:
        if r.info.lifecycle_stage != "deleted":
            return False
    return True


def delete_experiments(mlflow):
    logger.info(f"deleting empty experiments")
    logger.info(f"loading experiments....")
    experiments = mlflow.search_experiments(max_results=5000, order_by=["creation_time ASC"],
                                            view_type=ViewType.ACTIVE_ONLY)
    logger.info(f"experiments {len(experiments)}")
    with Progress() as progress:
        task1 = progress.add_task("Deleting runs...", total=len(experiments))
        for j, e in enumerate(experiments):
            runs = mlflow.search_runs(experiment_ids=[e.experiment_id], max_results=5000, order_by=["start_time DESC"],
                                      output_format="list", run_view_type=ViewType.ACTIVE_ONLY)
            logger.info(f"experiment {e.name}: runs {len(runs)}")
            if all_deleted(runs):
                logger.info(f"{j} delete {e.experiment_id} {e.name} {e.creation_time}")
                mlflow.delete_experiment(e.experiment_id)
            else:
                logger.info(f"experiment {e.name}: skip delete")
            progress.update(task1, advance=1)


def main(argv):
    parser = argparse.ArgumentParser(description="Clean old data",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--run", nargs='?', required=True,
                        help="Command: runs/experiments (delete old runs/empty experiments)")
    args = parser.parse_args(args=argv)
    logger.info("Starting")
    params = Params()
    logger.info(f"version : {params.version}")
    logger.info(f"workspace_name : {params.workspace_name}")
    logger.info(f"subscription_id : {params.subscription_id}")

    logger.info("Init client")
    client = init_client(params)

    workspace = client.workspaces.get(params.workspace_name)
    import mlflow
    mlflow.set_tracking_uri(workspace.mlflow_tracking_uri)
    logger.info(f"workspace.mlflow_tracking_uri={workspace.mlflow_tracking_uri}")

    if args.run == "runs":
        to_date = datetime.now(timezone.utc) - timedelta(hours=24 * 40)
        logger.info(f"Delete runs older than {to_date}")
        delete_runs(mlflow, to_date)
    if args.run == "experiments":
        logger.info(f"Delete empty experiments")
        delete_experiments(mlflow)
    logger.info("Done")


logger.info("Done")

if __name__ == "__main__":
    main(sys.argv[1:])
