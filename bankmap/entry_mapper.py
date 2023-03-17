import os

from bankmap.data import LEntry
from bankmap.loaders.apps import load_customer_apps, load_vendor_apps
from bankmap.loaders.ledgers import load_gls, load_ba, load_vendor_sfs, load_customer_sfs
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

    customer_sf_df = load_customer_sfs(os.path.join(data_dir, "Customer_Ledger_Entries.csv"),
                                       os.path.join(data_dir, "Customer_Bank_Accounts.csv"),
                                       os.path.join(data_dir, "Customers.csv"))
    res_info["Customer_Ledger_Entries"] = len(customer_sf_df)

    vendor_sf_df = load_vendor_sfs(os.path.join(data_dir, "Vendor_Ledger_Entries.csv"),
                                   os.path.join(data_dir, "Vendor_Bank_Accounts.csv"),
                                   os.path.join(data_dir, "Vendors.csv"))
    res_info["Vendor_Ledger_Entries"] = len(vendor_sf_df)

    gl_df = load_gls(os.path.join(data_dir, "GL_Accounts.csv"))
    res_info["GL_Accounts"] = len(gl_df)

    ba_df = load_ba(os.path.join(data_dir, "Bank_Accounts.csv"))
    res_info["Bank_Accounts"] = len(ba_df)

    l_entries = [LEntry(customer_sf_df.iloc[i]) for i in range(len(customer_sf_df))] + \
                [LEntry(vendor_sf_df.iloc[i]) for i in range(len(vendor_sf_df))] + \
                [LEntry(gl_df.iloc[i]) for i in range(len(gl_df))] + \
                [LEntry(ba_df.iloc[i]) for i in range(len(ba_df))]

    customer_apps_df = load_customer_apps(os.path.join(data_dir, "Customer_Applications.csv"), l_entries)
    res_info["Customer_Applications"] = len(customer_apps_df)

    vendor_apps_df = load_vendor_apps(os.path.join(data_dir, "Vendor_Applications.csv"), l_entries)
    res_info["Vendor_Applications"] = len(vendor_apps_df)
    res_info["l_entries"] = len(l_entries)

    return {}, res_info
