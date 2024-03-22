import pandas as pd
from jsonlines import jsonlines

from bankmap.data import e_str, Entry, PaymentType, Recognition, LType, e_str_ne, e_date_ne
from bankmap.logger import logger


# loads data from Customer_Recognitions or Vendor_Recognitions
# returns map of [statement no][[[mapper_internal doss], customer_no]]
# _type = [Cust, Vend]
def load_docs_map(file_name, _type: str):
    logger.info("loading entries {}".format(file_name))
    # skip = 0
    res = {}
    with jsonlines.open(file_name) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")
            try:
                id = e_str_ne(d, 'externalDocumentNumber')
                cv = e_str_ne(d, 'recognizedAccountNumber')
                iid = e_str_ne(d, 'appliedDocumentNumber')
                ra = res.get(id, (set(), cv))
                ra[0].add(iid)
                res[id] = ra
            except BaseException as err:
                raise RuntimeError(f"wrong data: {str(err)}")

    logger.info(f"loaded entries {len(res)} rows")
    # logger.debug("skipped future docs: {}".format(skip))
    return res


# loads data from Bank_Account_Recognitions
# returns map [statement no][Recognized]
def load_bank_recognitions_map(file_name):
    logger.info("loading {}".format(file_name))
    res = {}
    with jsonlines.open(file_name) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")
            if not LType.supported(e_str_ne(d, 'balAccountType')):
                continue
            no = e_str(d.get('statementExternalDocumentNumber'))
            if no not in res:
                res[no] = Recognition(_type=e_str_ne(d, 'balAccountType'), no=e_str_ne(d, 'balAccountNumber'))
    logger.info("loaded bankAccountRecognitions {} rows".format(len(res)))
    return res


def is_recognized(param):
    if param or param.strip() != "":
        if param != "91":  # special clients ID //todo workaround
            return True
    return False


def iban(p):
    if e_str(p.get('creditorIban')):
        return e_str(p.get('creditorIban'))
    return e_str(p.get('debtorIban'))


entry_cols = ['Description', 'Message', 'CdtDbtInd', 'Amount', 'Date', 'IBAN', 'E2EId',
              'RecAccount', 'Currency', 'RecDocs', 'DocNo', 'RecType', 'BankAccount']


# loads data from Bank_Statement_Entries
def load_entries(file_name, ba_map, cv_map):
    logger.info("loading {}".format(file_name))
    res = []
    found = set()
    with jsonlines.open(file_name) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")

            ext_id = e_str(d.get('externalDocumentNumber'))
            if ext_id in found:
                continue
            found.add(ext_id)
            rec_no, tp = '', LType.from_s('')
            t_rec = ba_map.get(ext_id, None)
            if t_rec:
                rec_no, tp = t_rec.no, t_rec.type
            docs = cv_map.get(ext_id, ("", ""))
            if docs[1] and docs[1] != rec_no:
                logger.info("change rec_no {} to {}".format(rec_no, docs[1]))
                rec_no = docs[1]

            if e_str(d.get('operationDate')) != '':
                res.append({'description': d.get('description'),
                            'message': d.get('messageToRecipient'),
                            'transactionType': PaymentType.from_s(e_str(d.get('transactionType'))),
                            'amount': d.get('amount'),
                            'date': e_date_ne(d, 'operationDate'),
                            'iban': iban(d),
                            'e2eId': d.get('endToEndId'),
                            'recAccount': rec_no,
                            'currency': d.get('accountCurrency'),
                            'recDocs': docs[0],
                            'recType': tp,
                            'externalDocumentNumber': d.get('externalDocumentNumber'),
                            'bankAccount': d.get('bankAccountNumber')
                            })
            else:
                logger.warn("no operation date: {}".format(d))
    # stable sort by date
    sr = [v for v in enumerate(res)]
    sr.sort(key=lambda e: (e[1]['date'].timestamp(), e[0]))
    res = [v[1] for v in sr]
    return res


def f_name(check, f1, f2):
    if check:
        return f1
    return f2


def non_empty_str(s1, s2):
    tmp = e_str(s1)
    if not tmp or tmp == '0':
        return s2
    return s1


# loads data from Bank_Statement_Lines
# returns Entries list
def load_lines(file_name):
    logger.info("loading {}".format(file_name))
    res = []
    found = set()
    with jsonlines.open(file_name) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")

            ext_id = e_str(d.get('externalDocumentNumber'))
            if ext_id in found:
                continue
            found.add(ext_id)
            credit = PaymentType.from_s(d['transactionType']) == PaymentType.CRDT

            if e_str(d.get('operationDate')) != '':
                value = {'description': d.get('description'),
                         'message': d.get('transactionText'),
                         'transactionType': PaymentType.from_s(e_str(d.get('transactionType'))),
                         'amount': d.get('statementAmount'),
                         'date': e_date_ne(d, 'operationDate'),
                         'iban': iban(d),
                         'e2eId': d.get('endToEndId'),
                         'recAccount': "",
                         'currency': d.get('accountCurrency'),
                         'recDocs': "",
                         'recType': LType.from_s(""),
                         'bankAccount': d.get('bankAccountNumber'),
                         'externalDocumentNumber': d.get('externalDocumentNumber'),
                         }
                res.append(Entry(value))
            else:
                logger.warn("no operation date: {}".format(d))
    # stable sort by date
    sr = [v for v in enumerate(res)]
    sr.sort(key=lambda e: (e[1].date.timestamp(), e[0]))
    res = [v[1] for v in sr]
    return res


# return unique company ibans - used for detecting company
def get_ibans(file_name):
    logger.info("loading entries {}".format(file_name))
    df = pd.read_csv(file_name, sep=',')
    logger.info("loaded entries {} rows".format(len(df)))

    res = [v for v in df[df["Acct_Id_IBAN"].notnull()]["Acct_Id_IBAN"].unique()]
    res += [v for v in df[df["Acct_Id_Othr_Id"].notnull()]["Acct_Id_Othr_Id"].unique()]
    return res
