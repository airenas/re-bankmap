import os
import tempfile
import zipfile

from bankmap.logger import logger


def copy_data(company, out_file):
    container_name, blob_service_client = get_data_client()
    if not blob_service_client:
        return

    file_name = "{}.zip".format(company)
    # Create a blob client using the local file name as the name for the blob
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
    with open(file=out_file, mode="rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    logger.info("Uploaded {}/{}".format(container_name, file_name))


def get_data_client():
    container_name = os.getenv('STORAGE_CONTAINER')
    if not container_name:
        logger.warn("No STORAGE_CONTAINER set")
        return None, None
    logger.info("container {}".format(container_name))
    connect_str = os.getenv('STORAGE_CONNECTION_STRING')
    if not connect_str:
        logger.warn("No STORAGE_CONNECTION_STRING set")
        return None, None
    from azure.storage.blob import BlobServiceClient
    return container_name, BlobServiceClient.from_connection_string(connect_str)


def load_data(company):
    container_name, blob_service_client = get_data_client()
    if not blob_service_client:
        return
    file_name = "{}.zip".format(company)
    logger.info("load {}/{}".format(container_name, file_name))
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
    return blob_client.download_blob().readall()


def save_extract_zip(data):
    temp_dir = tempfile.TemporaryDirectory()
    logger.info("tmp dir {}".format(temp_dir.name))
    out_file = os.path.join(temp_dir.name, "in.zip")
    logger.info("out_file {}".format(out_file))
    with open(out_file, "wb") as f:
        f.write(data)
    logger.info("saved file {} ({}b)".format(out_file, len(data)))
    data_dir = os.path.join(temp_dir.name, "data")
    with zipfile.ZipFile(out_file) as z:
        z.extractall(data_dir)
    return data_dir, out_file, temp_dir
