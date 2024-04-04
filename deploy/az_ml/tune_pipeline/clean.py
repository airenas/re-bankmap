import argparse
import os
import sys
from datetime import datetime, timezone, timedelta
from multiprocessing import Queue, Process

from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from mlflow import MlflowClient
from mlflow.entities import ViewType
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, TimeElapsedColumn, MofNCompleteColumn

log_f = print


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


def delete_worker(queue: Queue, mlflow_client, num):
    while True:
        (name, item) = queue.get()
        if name == "exit":
            print(f"exit {num}")
            break
        elif name == "run":
            r_date = datetime.fromtimestamp(item.info.start_time / 1000, tz=timezone.utc)
            r_name = item.data.tags.get('mlflow.note.content', item.data.tags.get('company', '??'))
            print(f"({num}) try delete {item.info.run_id}, state = {item.info.lifecycle_stage}")
            mlflow_client.delete_run(item.info.run_id)
            print(f"({num}) deleted {r_date} {r_name} {item.info.run_id}")
        elif name == "exp":
            print(f"{num} try delete {item.experiment_id} {item.name} {item.creation_time}")
            mlflow_client.delete_experiment(item.experiment_id)
            print(f"{num} deleted {item.experiment_id} {item.name} {item.creation_time}")
        else:
            raise Exception(f"unknown delete task {name}")


# return non deleted runs
def delete_runs(to_date, experiments, name, mlflow_client: MlflowClient, queue):
    log_f(f"loading runs....")
    from_date = to_date - timedelta(hours=24 * 20)
    unix_timestamp = datetime.timestamp(from_date) * 1000
    filter_str = f'attributes.start_time > "{int(unix_timestamp)}"'
    runs = mlflow_client.search_runs(experiment_ids=experiments, max_results=10000, order_by=["start_time DESC"],
                                     filter_string=filter_str,
                                     run_view_type=ViewType.ACTIVE_ONLY)
    log_f(f"runs {len(runs)}")
    count = 0
    for r in runs:
        if is_ok(r, to_date):
            count += 1

    log_f(f"deleting {count}")

    res = []
    for j, r in enumerate(runs):
        r_date = datetime.fromtimestamp(r.info.start_time / 1000, tz=timezone.utc)
        r_name = r.data.tags.get('mlflow.note.content', r.data.tags.get('company', '??'))
        if is_ok(r, to_date):
            log_f(f"{j} mark to delete {r_date} {r_name} {r.info.run_id}")
            queue.put(("run", r))
        elif not is_deleted(r):
            res.append(r)
    log_f(f"non deletable {len(res)}")
    return res


def delete_experiments(to_date, opw: ProgressWrap, mlflow_client: MlflowClient, queue):
    log_f(f"deleting empty experiments")
    log_f(f"loading experiments....")
    experiments = mlflow_client.search_experiments(max_results=5000, order_by=["creation_time ASC"],
                                                   view_type=ViewType.ALL)
    log_f(f"experiments {len(experiments)}")
    opw.progress.update(opw.task, description=f"Deleting experiments...", total=len(experiments))
    for j, e in enumerate(experiments):
        runs = delete_runs(to_date, [e.experiment_id], e.name, mlflow_client, queue)
        if len(runs) == 0:
            log_f(f"{j} mark to delete {e.experiment_id} {e.name} {e.creation_time}")
            queue.put(("exp", e))
        else:
            log_f(f"experiment {e.name}: skip delete")
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
    log_f("Starting")
    params = Params()
    log_f(f"version : {params.version}")
    log_f(f"workspace_name : {params.workspace_name}")
    log_f(f"subscription_id : {params.subscription_id}")

    log_f("Init client")
    client = init_client(params)

    workspace = client.workspaces.get(params.workspace_name)
    log_f(f"workspace.mlflow_tracking_uri={workspace.mlflow_tracking_uri}")
    mlflow_client = MlflowClient(tracking_uri=workspace.mlflow_tracking_uri)

    to_date = datetime.now(timezone.utc) - timedelta(hours=24 * args.days)

    progress = Progress(*Progress.get_default_columns(), TimeElapsedColumn(), MofNCompleteColumn())
    overall_progress = Progress(*Progress.get_default_columns(), TimeElapsedColumn(), MofNCompleteColumn())

    progress_group = Group(Panel(Group(progress)), Panel(Group(overall_progress)), )
    overall_task = overall_progress.add_task("Deleting exps...", total=100)

    queue = Queue()
    num_workers = 10
    processes = [Process(target=delete_worker, args=(queue, mlflow_client, i)) for i in range(num_workers)]
    for process in processes:
        process.start()

    with Live(progress_group, refresh_per_second=4):
        if args.run == "runs":
            log_f(f"Delete runs older than {to_date}")
            delete_runs(to_date, [], "all exps")
        if args.run == "experiments":
            log_f(f"Delete empty experiments")
            delete_experiments(to_date, ProgressWrap(overall_progress, overall_task),
                               mlflow_client, queue)

    for _ in range(num_workers):
        queue.put(("exit", None))
    for process in processes:
        process.join()
    log_f("Done")


log_f("Done")

if __name__ == "__main__":
    main(sys.argv[1:])
