import os

from bankmap.logger import logger
from bankmap.transformers.entry import load_docs_map


def do_mapping(data_dir, company: str):
    logger.info("data dir {}", data_dir)
    c_docs_map = load_docs_map(os.path.join(data_dir, "Customer_Recognitions.csv"), "Cust")
    v_docs_map = load_docs_map(os.path.join(data_dir, "Vendor_Recognitions.csv"), "Vend")
    res_info = {}
    res_info["Customer_Recognitions"] = len(c_docs_map)
    res_info["Vendor_Recognitions"] = len(v_docs_map)
    return {}, res_info
