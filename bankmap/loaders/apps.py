import pandas as pd

from bankmap.data import e_currency
from bankmap.logger import logger

app_cols = ['Type', 'Apply_Date', 'Apply_Amount', 'Remaining_Amount', 'Document_No', 'CV_No']


def prepare_cust_apps(df, l_map):
    res = []
    data = df.to_dict('records')
    for d in data:
        doc = d['Document_No_']
        cv_no = l_map.get(doc, "")
        date = d['Application_Created_Date']
        if date == "0":  # close same day if not set
            date = d['Posting_Date']
        if cv_no:
            res.append(['Customer', date,
                        e_currency(d['Application_Amount']),
                        e_currency(d['Remaining_Amount']),
                        doc, cv_no
                        ])
    return pd.DataFrame(res, columns=app_cols)


# loads customer apps
# returns dataframe
def load_customer_apps(apps_file_name, l_entries):
    logger.info("loading apps {}".format(apps_file_name))
    ledgers = pd.read_csv(apps_file_name, sep=',')
    l_map = {e.doc_no: e.id for e in l_entries}
    return prepare_cust_apps(ledgers, l_map)


def prepare_vend_apps(df, l_map):
    res = []
    data = df.to_dict('records')
    for d in data:
        doc = d['Document_No_']
        cv_no = l_map.get(doc, "")
        date = d['Application_Created_Date']
        if date == "0":  # close same day if not set
            date = d['Posting_Date']
        if cv_no:
            res.append(['Vendor', date,
                        e_currency(d['Application_Amount']),
                        e_currency(d['Remaining_Amount']),
                        doc, cv_no
                        ])
    return pd.DataFrame(res, columns=app_cols)


# loads vendor apps
# returns dataframe
def load_vendor_apps(apps_file_name, l_entries):
    logger.info("loading apps {}".format(apps_file_name))
    ledgers = pd.read_csv(apps_file_name, sep=',')
    l_map = {e.doc_no: e.id for e in l_entries}
    return prepare_vend_apps(ledgers, l_map)
