import pandas as pd
from tqdm import tqdm

from bankmap.data import e_currency
from bankmap.logger import logger

app_cols = ['Type', 'Apply_Date', 'Apply_Amount', 'Remaining_Amount', 'Document_No', 'CV_No']


def prepare_cust_apps(df, l_map):
    res = []
    with tqdm("format data", total=len(df)) as pbar:
        for i in range(len(df)):
            doc = df['Document_No_'].iloc[i]
            cv_no = l_map.get(doc, "")
            date = df['Application_Created_Date'].iloc[i]
            if date == "0":  # close same day if not set
                date = df['Posting_Date'].iloc[i]
            pbar.update(1)
            if cv_no:
                res.append(['Customer', date,
                            e_currency(df['Application_Amount'].iloc[i]),
                            e_currency(df['Remaining_Amount'].iloc[i]),
                            doc, cv_no
                            ])
    return pd.DataFrame(res, columns=app_cols)


# loads customer apps
# returns dataframe
def load_customer_apps(apps_file_name, l_entries):
    logger.info("loading apps {}".format(apps_file_name))
    ledgers = pd.read_csv(apps_file_name, sep=',')
    l_map = {l.doc_no: l.id for l in l_entries}
    return prepare_cust_apps(ledgers, l_map)


def prepare_vend_apps(df, l_map):
    res = []
    with tqdm("format data", total=len(df)) as pbar:
        for i in range(len(df)):
            doc = df['Document_No_'].iloc[i]
            cv_no = l_map.get(doc, "")
            date = df['Application_Created_Date'].iloc[i]
            if date == "0":  # close same day if not set
                date = df['Posting_Date'].iloc[i]
            pbar.update(1)
            if cv_no:
                res.append(['Vendor', date,
                            e_currency(df['Application_Amount'].iloc[i]),
                            e_currency(df['Remaining_Amount'].iloc[i]),
                            doc, cv_no
                            ])
    return pd.DataFrame(res, columns=app_cols)


# loads vendor apps
# returns dataframe
def load_vendor_apps(apps_file_name, l_entries):
    logger.info("loading apps {}".format(apps_file_name))
    ledgers = pd.read_csv(apps_file_name, sep=',')
    l_map = {l.doc_no: l.id for l in l_entries}
    return prepare_vend_apps(ledgers, l_map)
