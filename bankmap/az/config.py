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
    container_name = os.getenv('DEBUG_STORAGE_CONFIG_CONTAINER')
    if not container_name:
        logger.warn("No DEBUG_STORAGE_CONFIG_CONTAINER set")
        return None
    connect_str = os.getenv('DEBUG_STORAGE_CONNECTION_STRING')
    if not connect_str:
        logger.warn("No DEBUG_STORAGE_CONNECTION_STRING set")
        return None
    logger.info("container {}".format(container_name))
    logger.debug("connect_str {}".format(connect_str))
    from azure.storage.blob import BlobServiceClient

    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    file_name = "{}.json".format(company)
    logger.info("load {}/{}".format(container_name, file_name))
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
    data = blob_client.download_blob().readall()
    logger.debug("data {}".format(str(data, "utf-8")))
    return PredictionCfg.from_dict(json.loads(str(data, "utf-8")))
