import argparse
import os
import sys
from datetime import datetime, timezone, timedelta

import mlflow
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from mlflow.entities import ViewType
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, TimeElapsedColumn, MofNCompleteColumn

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
    return r_date < to_date and not is_deleted(run)


def is_deleted(run):
    return run.info.lifecycle_stage == "deleted"


class ProgressWrap:
    def __init__(self, progress, task):
        self.task = task
        self.progress = progress


# return non deleted runs
def delete_runs(to_date, experiments, name, pw: ProgressWrap):
    logger.info(f"deleting to {to_date}")
    logger.info(f"loading runs....")
    from_date = to_date - timedelta(hours=24 * 20)
    unix_timestamp = datetime.timestamp(from_date) * 1000
    filter_str = f'attributes.start_time > "{int(unix_timestamp)}"'
    logger.info(f"filter_str {filter_str}")
    runs = mlflow.search_runs(experiment_ids=experiments, max_results=10000, order_by=["start_time ASC"],
                              filter_string=filter_str,
                              output_format="list", run_view_type=ViewType.ACTIVE_ONLY,
                              search_all_experiments=True)
    logger.info(f"runs {len(runs)}")
    count = 0
    for r in runs:
        if is_ok(r, to_date):
            count += 1

    logger.info(f"deleting {count}")

    res = []
    pw.progress.update(pw.task, description=f"Deleting runs for {name}...", total=count)
    pw.progress.update(pw.task, completed=0)
    for j, r in enumerate(runs):
        r_date = datetime.fromtimestamp(r.info.start_time / 1000, tz=timezone.utc)
        r_name = r.data.tags.get('mlflow.note.content', r.data.tags.get('company', '??'))
        if is_ok(r, to_date):
            print(f"{j} delete {r_date} {r_name} {r.info.run_id}")
            mlflow.delete_run(r.info.run_id)
            pw.progress.update(pw.task, advance=1)
        elif not is_deleted(r):
            res.append(r)
    return res


def delete_experiments(to_date, opw: ProgressWrap, pw: ProgressWrap):
    logger.info(f"deleting empty experiments")
    logger.info(f"loading experiments....")
    experiments = mlflow.search_experiments(max_results=5000, order_by=["creation_time ASC"],
                                            view_type=ViewType.ACTIVE_ONLY)
    logger.info(f"experiments {len(experiments)}")
    opw.progress.update(opw.task, description=f"Deleting experiments...", total=len(experiments))
    for j, e in enumerate(experiments):
        runs = delete_runs(to_date, [e.experiment_id], e.name, pw)
        if len(runs) == 0:
            print(f"{j} delete {e.experiment_id} {e.name} {e.creation_time}")
            mlflow.delete_experiment(e.experiment_id)
        else:
            print(f"experiment {e.name}: skip delete")
        opw.progress.update(opw.task, advance=1)


def main(argv):
    parser = argparse.ArgumentParser(description="Clean old data",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--run", nargs='?', required=True,
                        help="Command: runs/experiments (delete old runs/empty experiments)")
    parser.add_argument("--days", nargs='?', type=int, default=20,
                        help="history in days to keep")
    args = parser.parse_args(args=argv)
    logger.info("Starting")
    params = Params()
    logger.info(f"version : {params.version}")
    logger.info(f"workspace_name : {params.workspace_name}")
    logger.info(f"subscription_id : {params.subscription_id}")

    logger.info("Init client")
    client = init_client(params)

    workspace = client.workspaces.get(params.workspace_name)
    mlflow.set_tracking_uri(workspace.mlflow_tracking_uri)
    logger.info(f"workspace.mlflow_tracking_uri={workspace.mlflow_tracking_uri}")

    to_date = datetime.now(timezone.utc) - timedelta(hours=24 * args.days)

    progress = Progress(*Progress.get_default_columns(), TimeElapsedColumn(), MofNCompleteColumn())
    overall_progress = Progress(*Progress.get_default_columns(), TimeElapsedColumn(), MofNCompleteColumn())

    progress_group = Group(Panel(Group(progress)), Panel(Group(overall_progress)), )
    task = progress.add_task("Deleting runs...", total=100)
    overall_task = overall_progress.add_task("Deleting exps...", total=100)

    with Live(progress_group, refresh_per_second=4):
        if args.run == "runs":
            logger.info(f"Delete runs older than {to_date}")
            delete_runs(to_date, [], "all exps",  ProgressWrap(progress, task))
        if args.run == "experiments":
            logger.info(f"Delete empty experiments")
            delete_experiments(to_date, ProgressWrap(overall_progress, overall_task),
                               ProgressWrap(progress, task))
    logger.info("Done")


logger.info("Done")

if __name__ == "__main__":
    main(sys.argv[1:])
