import json
import os

from bankmap.cfg import PredictionCfg
from bankmap.logger import logger


def load_config_or_default(company):
    try:
        res = load_config(company)
        if res:
            return res
    except BaseException as err:
        logger.warn(err)
    return PredictionCfg.default(company)


def load_config(company):
    container_name = os.getenv('DEBUG_STORAGE_CONFIG_CONTAINER')
    if not container_name:
        logger.warn("No DEBUG_STORAGE_CONFIG_CONTAINER set")
        return None
    connect_str = os.getenv('DEBUG_STORAGE_CONNECTION_STRING')
    if not connect_str:
        logger.warn("No DEBUG_STORAGE_CONNECTION_STRING set")
        return None
    logger.info("container {}".format(container_name))
    from azure.storage.blob import BlobServiceClient

    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    file_name = "{}.json".format(company)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
    logger.info("Load{}".format(file_name))
    data = blob_client.download_blob(file_name).readall()
    return PredictionCfg.from_dict(json.load(data))
