import json
import os

from bankmap.cfg import PredictionCfg
from bankmap.logger import logger


def load_config_or_default(company):
    try:
        res = load_config(company)
        if res:
            logger.info("config loaded {}".format(res))
            res.company = company  # make sure we have company
            return res
    except BaseException as err:
        logger.error("Can't load config for {}, {}".format(company, str(err)))
        logger.warn("using default config")
    return PredictionCfg.default(company)


def load_config(company):
    container_name, blob_service_client = get_config_client()
    if not blob_service_client:
        return
    file_name = "{}.json".format(company)
    logger.info("load {}/{}".format(container_name, file_name))
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
    data = blob_client.download_blob().readall()
    logger.debug("data {}".format(str(data, "utf-8")))
    return PredictionCfg.from_dict(json.loads(str(data, "utf-8")))


def get_config_client():
    container_name = os.getenv('STORAGE_CONFIG_CONTAINER')
    if not container_name:
        logger.warn("No STORAGE_CONFIG_CONTAINER set")
        return None, None
    logger.info("container {}".format(container_name))
    connect_str = os.getenv('STORAGE_CONNECTION_STRING')
    if not connect_str:
        logger.warn("No STORAGE_CONNECTION_STRING set")
        return None, None
    from azure.storage.blob import BlobServiceClient
    return container_name, BlobServiceClient.from_connection_string(connect_str)


def save_config(cfg: PredictionCfg, company):
    container_name, blob_service_client = get_config_client()
    if not blob_service_client:
        return
    file_name = "{}.json".format(company)
    # Create a blob client using the local file name as the name for the blob
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
    blob_client.upload_blob(json.dumps(cfg.to_dic(), ensure_ascii=False, indent=2), overwrite=True)
    logger.info("Uploaded {}/{}".format(container_name, file_name))
