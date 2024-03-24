import pandas as pd
from jsonlines import jsonlines

from bankmap.data import e_str, e_date, e_currency, e_float, MapType, DocType, LType, e_str_ne
from bankmap.logger import logger


def load_IBANs(file_name, _type):
    logger.info("loading {}".format(file_name))
    res = {}
    with jsonlines.open(file_name) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")
            cust = e_str(d.get(_type + 'Number'))
            no = e_str(d.get('bankAccountNumber'))  # TODO
            res[cust] = no
    logger.info(f"loaded {len(res)} rows in {file_name}")
    return res


def load_cust_names(file_name):
    logger.info("loading {}".format(file_name))
    res = {}
    with jsonlines.open(file_name) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")
            cust = e_str_ne(d, 'number')
            name = e_str(d.get('name'))
            method = MapType.from_s(e_str(d.get('applicationMethod')))
            res[cust] = (name, method)
    logger.info(f"loaded {len(res)} rows in {file_name}")
    return res


def load_customer_sfs(ledgers_file_name, ba_file_name, cust_file_name):
    ibans = load_IBANs(ba_file_name, 'customer')
    names = load_cust_names(cust_file_name)

    logger.info("loading {}".format(ledgers_file_name))
    res = []
    with jsonlines.open(ledgers_file_name) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")
            dt = e_str(d['documentType'])
            if not dt or DocType.skip(dt):
                continue
            _id = e_str_ne(d, 'customerNumber')
            cd = names[_id]
            res.append({'type': LType.CUST.to_s(), "number": _id, 'name': cd[0],
                        'iban': ibans.get(_id, ''), 'documentNumber': d['documentNumber'],
                        'dueDate': e_date(d, 'dueDate'),
                        'documentDate': e_date(d,'documentDate'),
                        'externalDocumentNumber': d['externalDocumentNumber'],
                        'amount': e_float(d, 'amount'),
                        'currencyCode': e_currency(d.get('currencyCode')),
                        'documentType': dt,
                        'closedAtDate': e_date(d, 'closedAtDate'),
                        'mapType': cd[1].to_s(),
                        'open': d['isOpen'],
                        'remainingAmount': d['remainingAmount']})

    return res


# loads vendor SF
def load_vendor_sfs(ledgers_file_name, ba_file_name, vend_file_name):
    ibans = load_IBANs(ba_file_name, 'vendor')
    names = load_cust_names(vend_file_name)

    logger.info("loading {}".format(ledgers_file_name))
    res = []
    with jsonlines.open(ledgers_file_name) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")
            dt = e_str(d['documentType'])
            if not dt or DocType.skip(dt):
                continue
            _id = e_str_ne(d, 'vendorNumber')
            cd = names[_id]
            res.append({'type': LType.VEND.to_s(), "number": _id, 'name': cd[0],
                        'iban': ibans.get(_id, ''), 'documentNumber': d['documentNumber'],
                        'dueDate': e_date(d,'dueDate'),
                        'documentDate': e_date(d,'documentDate'),
                        'externalDocumentNumber': d['externalDocumentNumber'],
                        'amount': e_float(d, 'amount'),
                        'currencyCode': e_currency(d.get('currencyCode')),
                        'documentType': dt,
                        'closedAtDate': e_date(d, 'closedAtDate'),
                        'mapType': cd[1].to_s(),
                        'open': d['isOpen'],
                        'remainingAmount': d['remainingAmount']})

    return res


# loads GL
# returns dataframe
def load_gls(ledgers_file_name):
    logger.info("loading {}".format(ledgers_file_name))
    res = []
    with jsonlines.open(ledgers_file_name) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")
            _id = e_str_ne(d, 'number')
            res.append({'type': LType.GL.to_s(), "number": _id,
                        'name': e_str(d.get('searchName')),  # TODO or name
                        'iban': '', 'documentNumber': '',
                        'dueDate': None,
                        'documentDate': None,
                        'externalDocumentNumber': '',
                        'amount': 0,
                        'currencyCode': 'EUR',
                        'documentType': LType.GL.to_s(),
                        'closedAtDate': None,
                        'mapType': MapType.UNUSED.to_s(),
                        'open': True,
                        'remainingAmount': 0})

    return res


# loads BA
# returns dataframe
def load_ba(ledgers_file_name):
    logger.info("loading {}".format(ledgers_file_name))
    res = []
    with jsonlines.open(ledgers_file_name) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")
            _id = e_str_ne(d, 'number')
            res.append({'type': LType.BA.to_s(), "number": _id,
                        'name': e_str(d.get('searchName')),  # TODO or name
                        'iban': e_str(d.get('iban')),
                        'documentNumber': '',
                        'dueDate': None,
                        'documentDate': None,
                        'externalDocumentNumber': '',
                        'amount': 0,
                        'currencyCode': e_currency(d.get('currencyCode')),
                        'documentType': LType.BA.to_s(),
                        'closedAtDate': None,
                        'mapType': MapType.UNUSED.to_s(),
                        'open': True,
                        'remainingAmount': 0})

    return res
