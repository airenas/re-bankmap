import pandas as pd
from tqdm import tqdm

from bankmap.data import e_str, e_date, e_currency, e_float, MapType
from bankmap.logger import logger

ledger_cols = ['Type', 'No', 'Name', 'IBAN', 'Document_No', 'Due_Date', 'Document_Date', 'ExtDoc', 'Amount',
               'Currency', 'Document_Type', 'Closed_Date', 'Map_Type']


def prepare_cust_sfs(df, c_data, accounts):
    res = []
    with tqdm("format cmp_matrix", total=len(df)) as pbar:
        for i in range(len(df)):
            pbar.update(1)
            dt = e_str(df['Document_Type'].iloc[i])
            if not dt or dt == "Mokėjimas":
                continue
            _id = df['Customer_No_'].iloc[i]
            cd = c_data[_id]
            res.append(['Customer', _id, cd[0], accounts.get(_id, ''), df['Document_No_'].iloc[i],
                        df['Due_Date'].iloc[i], df['Document_Date'].iloc[i],
                        df['External_Document_No_'].iloc[i],
                        e_float(df['Amount'].iloc[i]),
                        e_currency(df['Currency_Code'].iloc[i]),
                        dt,
                        e_date(df['ClosedAtDate'].iloc[i]), cd[1].to_s()])
    return pd.DataFrame(res, columns=ledger_cols)


# loads customer SF
# returns dataframe
def load_customer_sfs(ledgers_file_name, ba_file_name, cust_file_name):
    logger.info("loading sfs {}".format(ledgers_file_name))
    ledgers = pd.read_csv(ledgers_file_name, sep=',')
    logger.info("loaded ledgers {} rows".format(len(ledgers)))
    accounts = pd.read_csv(ba_file_name, sep=',')
    logger.info("loaded ba {} rows".format(len(accounts)))
    names = pd.read_csv(cust_file_name, sep=',')
    logger.info("loaded sfs {} rows".format(len(names)))

    c_d = {r['No_']: (r['Name'], MapType.from_s(r['Application_Method'])) for _, r in names.iterrows()}
    accounts_d = {r['Customer_No_']: r['Bank_Account_No_'] for _, r in accounts.iterrows()}

    return prepare_cust_sfs(ledgers, c_d, accounts_d)


def prepare_vend_sfs(df, v_data, accounts):
    res = []
    with tqdm("format cmp_matrix", total=len(df)) as pbar:
        for i in range(len(df)):
            pbar.update(1)
            dt = e_str(df['Document_Type'].iloc[i])
            if not dt or dt == "Mokėjimas":
                continue
            _id = df['Vendor_No_'].iloc[i]
            vd = v_data[_id]
            res.append(['Vendor', _id, vd[0], accounts.get(_id, ''), df['Document_No_'].iloc[i],
                        df['Due_Date'].iloc[i],
                        df['Document_Date'].iloc[i], df['External_Document_No_'].iloc[i],
                        df['Amount'].iloc[i],
                        e_currency(df['Currency_Code'].iloc[i]),
                        dt,
                        e_date(df['ClosedAtDate'].iloc[i]), vd[1].to_s()])
    return pd.DataFrame(res, columns=ledger_cols)


# loads vendor SF
# returns dataframe
def load_vendor_sfs(ledgers_file_name, ba_file_name, vend_file_name):
    logger.info("loading sfs {}".format(ledgers_file_name))
    ledgers = pd.read_csv(ledgers_file_name, sep=',')
    logger.info("loaded ledgers {} rows".format(len(ledgers)))
    accounts = pd.read_csv(ba_file_name, sep=',')
    logger.info("loaded ba {} rows".format(len(accounts)))
    names = pd.read_csv(vend_file_name, sep=',')
    logger.info("loaded sfs {} rows".format(len(names)))

    c_d = {r['No_']: (r['Name'], MapType.from_s(r['Application_Method'])) for _, r in names.iterrows()}
    accounts_d = {r['Vendor_No_']: r['Bank_Account_No_'] for _, r in accounts.iterrows()}

    return prepare_vend_sfs(ledgers, c_d, accounts_d)


# loads GL
# returns dataframe
def load_gls(ledgers_file_name):
    logger.info("loading gls {}".format(ledgers_file_name))
    ledgers = pd.read_csv(ledgers_file_name, sep=',')
    res = []
    with tqdm("load gl", total=len(ledgers)) as pbar:
        for i in range(len(ledgers)):
            pbar.update(1)
            _id = ledgers['No_'].iloc[i]
            res.append(['GL', _id, ledgers['Search_Name'].iloc[i], '', '',
                        '',
                        '', '', 0, 'EUR', 'GL', '', MapType.UNUSED.to_s()])
    return pd.DataFrame(res, columns=ledger_cols)


# loads BA
# returns dataframe
def load_ba(ledgers_file_name):
    logger.info("loading ba {}".format(ledgers_file_name))
    ledgers = pd.read_csv(ledgers_file_name, sep=',')
    res = []
    with tqdm("load gl", total=len(ledgers)) as pbar:
        for i in range(len(ledgers)):
            pbar.update(1)
            _id = ledgers['No_'].iloc[i]
            res.append(['BA', _id, ledgers['Search_Name'].iloc[i], ledgers['IBAN'].iloc[i], '',
                        '',
                        '', '', 0, e_currency(ledgers['Currency_Code'].iloc[i]),
                        'BA', '', MapType.UNUSED.to_s()])
    return pd.DataFrame(res, columns=ledger_cols)
