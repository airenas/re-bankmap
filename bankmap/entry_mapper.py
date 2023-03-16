import os

from bankmap.logger import logger
from bankmap.transformers.entry import load_docs_map, load_bank_recognitions_map, load_entries


def do_mapping(data_dir, company: str):
    logger.info("data dir {}".format(data_dir))
    c_docs_map = load_docs_map(os.path.join(data_dir, "Customer_Recognitions.csv"), "Cust")
    v_docs_map = load_docs_map(os.path.join(data_dir, "Vendor_Recognitions.csv"), "Vend")
    res_info = {}
    res_info["Customer_Recognitions"] = len(c_docs_map)
    res_info["Vendor_Recognitions"] = len(v_docs_map)

    cv_docs_map = c_docs_map
    cv_docs_map.update(v_docs_map)

    ba_map = load_bank_recognitions_map(os.path.join(data_dir, "Bank_Account_Recognitions.csv"))
    res_info["Bank_Account_Recognitions"] = len(ba_map)

    entries_df = load_entries(os.path.join(data_dir, "Bank_Statement_Entries.csv"), ba_map, c_docs_map)
    res_info["Bank_Statement_Entries"] = len(entries_df)

    return {}, res_info
