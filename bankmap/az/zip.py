import os
import tempfile
import zipfile

from bankmap.logger import logger


def copy_data(company, file):
    file_name = "{}.zip".format(company)
    upload_file(file_name, get_container_name("STORAGE_CONTAINER"), file)


def upload_file(storage_file_name, container_name, file):
    if not storage_file_name:
        return
    blob_service_client = get_client()
    if not blob_service_client:
        return

    # Create a blob client using the local file name as the name for the blob
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=storage_file_name)
    with open(file=file, mode="rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    logger.info("Uploaded {}/{}".format(container_name, storage_file_name))


def get_container_name(env_name):
    container_name = os.getenv(env_name)
    if not container_name:
        logger.warn("No {} set".format(env_name))
        return None
    return container_name


def get_client():
    connect_str = os.getenv('STORAGE_CONNECTION_STRING')
    if not connect_str:
        logger.warn("No STORAGE_CONNECTION_STRING set")
        return None
    from azure.storage.blob import BlobServiceClient
    return BlobServiceClient.from_connection_string(connect_str)


def load_data(company):
    container_name, blob_service_client = get_container_name("STORAGE_CONTAINER"), get_client()
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
