import pandas as pd

from bankmap.data import e_str, e_date, e_currency, e_float, MapType, DocType
from bankmap.logger import logger

ledger_cols = ['Type', 'No', 'Name', 'IBAN', 'Document_No', 'Due_Date', 'Document_Date', 'ExtDoc', 'Amount',
               'Currency', 'Document_Type', 'Closed_Date', 'Map_Type', 'Open', 'Remaining_Amount']


def prepare_cust_sfs(df, c_data, accounts):
    res = []
    data = df.to_dict('records')
    for d in data:
        dt = e_str(d['Document_Type'])
        if not dt or DocType.skip(dt):
            continue
        _id = d['Customer_No_']
        cd = c_data[_id]
        res.append(['Customer', _id, cd[0], accounts.get(_id, ''), d['Document_No_'],
                    d['Due_Date'], d['Document_Date'],
                    d['External_Document_No_'],
                    e_float(d['Amount']),
                    e_currency(d['Currency_Code']),
                    dt,
                    e_date(d['ClosedAtDate']), cd[1].to_s(), d['Open'], d['Remaining_Amount']])
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

    c_d = {r['No_']: (r['Name'], MapType.from_s(r['Application_Method'])) for r in names.to_dict('records')}
    accounts_d = {r['Customer_No_']: r['Bank_Account_No_'] for r in accounts.to_dict('records')}

    return prepare_cust_sfs(ledgers, c_d, accounts_d)


def prepare_vend_sfs(df, v_data, accounts):
    res = []
    data = df.to_dict('records')
    for d in data:
        dt = e_str(d['Document_Type'])
        if not dt or DocType.skip(dt):
            continue
        _id = d['Vendor_No_']
        vd = v_data[_id]
        res.append(['Vendor', _id, vd[0], accounts.get(_id, ''), d['Document_No_'],
                    d['Due_Date'],
                    d['Document_Date'], d['External_Document_No_'],
                    d['Amount'],
                    e_currency(d['Currency_Code']),
                    dt,
                    e_date(d['ClosedAtDate']), vd[1].to_s(), d['Open'], d['Remaining_Amount']])
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

    c_d = {r['No_']: (r['Name'], MapType.from_s(r['Application_Method'])) for r in names.to_dict('records')}
    accounts_d = {r['Vendor_No_']: r['Bank_Account_No_'] for r in accounts.to_dict('records')}

    return prepare_vend_sfs(ledgers, c_d, accounts_d)


# loads GL
# returns dataframe
def load_gls(ledgers_file_name):
    logger.info("loading gls {}".format(ledgers_file_name))
    df = pd.read_csv(ledgers_file_name, sep=',')
    res = []
    data = df.to_dict('records')
    for d in data:
        _id = d['No_']
        res.append(['GL', _id, d['Search_Name'], '', '',
                    '',
                    '', '', 0, 'EUR', 'GL', '', MapType.UNUSED.to_s(), '', 0])
    return pd.DataFrame(res, columns=ledger_cols)


# loads BA
# returns dataframe
def load_ba(ledgers_file_name):
    logger.info("loading ba {}".format(ledgers_file_name))
    df = pd.read_csv(ledgers_file_name, sep=',')
    res = []
    data = df.to_dict('records')
    for d in data:
        _id = d['No_']
        res.append(['BA', _id, d['Search_Name'], d['IBAN'], '',
                    '',
                    '', '', 0, e_currency(d['Currency_Code']),
                    'BA', '', MapType.UNUSED.to_s(), '', 0])
    return pd.DataFrame(res, columns=ledger_cols)
