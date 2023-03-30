import pandas as pd

from bankmap.data import e_str, e_date, to_date, e_currency, e_float, Entry, PaymentType, Recognition, LType
from bankmap.logger import logger


# loads data from Customer_Recognitions or Vendor_Recognitions
# returns map of [statement no][[[mapper_internal doss], customer_no]]
# _type = [Cust, Vend]
def load_docs_map(file_name, _type: str):
    logger.info("loading entries {}".format(file_name))
    df = pd.read_csv(file_name, sep=',')
    logger.info("loaded entries {} rows".format(len(df)))
    logger.debug("{}".format(df.head(n=10)))
    logger.debug("Headers: {}".format(list(df)))
    skip = 0
    res = {}
    data = df.to_dict('records')
    for d in data:
        id = e_str(d['Statement_External_Document_No_'])
        st_date = e_date(d[_type + '_Posting_Date'])
        doc_date = e_date(d['Applied_' + _type + '_Document_Date'])
        cv = e_str(d['Vend_Vendor_No_' if _type == "Vend" else 'Cust_Customer_No_'])
        if st_date < doc_date:
            skip += 1
            continue
        iid = e_str(d['Applied_' + _type + '_Document_No_'])
        ra = res.get(id, (set(), cv))
        ra[0].add(iid)
        res[id] = ra
    logger.debug("skipped future docs: {}".format(skip))
    return res


# loads data from Bank_Account_Recognitions
# returns map [statement no][Recognized]
def load_bank_recognitions_map(file_name):
    logger.info("loading Bank_Account_Recognitions {}".format(file_name))
    df = pd.read_csv(file_name, sep=',')
    logger.info("loaded Bank_Account_Recognitions {} rows".format(len(df)))
    logger.debug("{}".format(df.head(n=10)))
    logger.debug("Headers: {}".format(list(df)))
    res = {}
    data = df.to_dict('records')
    for d in data:
        no = e_str(d['Statement_External_Document_No_'])
        if not no in res:
            res[no] = Recognition(_type=e_str(d['Bal__Account_Type']), no=e_str(d['Bal__Account_No_']))
    return res


def is_recognized(param):
    if param or param.strip() != "":
        if param != "91":  # special clients ID //todo workaround
            return True
    return False


def iban(p):
    if p["N_ND_TD_RP_DbtrAcct_Id_IBAN"] != p["N_ND_TD_RP_DbtrAcct_Id_IBAN"]:
        return p["N_ND_TD_RP_CdtrAcct_Id_IBAN"]
    return p["N_ND_TD_RP_DbtrAcct_Id_IBAN"]


entry_cols = ['Description', 'Message', 'CdtDbtInd', 'Amount', 'Date', 'IBAN', 'E2EId',
              'RecAccount', 'RecDoc', 'Currency', 'Docs', 'DocNo', 'RecType', 'BankAccount']


# loads data from Bank_Statement_Entries
# returns panda table
def load_entries(file_name, ba_map, cv_map):
    logger.info("loading entries {}".format(file_name))
    df = pd.read_csv(file_name, sep=',')
    logger.info("loaded entries {} rows".format(len(df)))
    logger.debug("{}".format(df.head(n=10)))
    hd = list(df)
    logger.debug("Headers: {}".format(hd))

    res = []

    found = set()
    data = df.to_dict('records')
    for d in data:
        ext_id = e_str(d['External_Document_No_'])
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

        res.append([d['Description'], d['Message_to_Recipient'], d['N_CdtDbtInd'],
                    e_float(d['N_Amt']), d['N_BookDt_Dt'], iban(d),
                    d['N_ND_TD_Refs_EndToEndId'],
                    rec_no,
                    d['Recognized_Document_No_'],
                    e_currency(d['Acct_Ccy']),
                    docs[0],
                    d['External_Document_No_'], tp.to_s(), d['Bank_Account_No_']])
    # stable sort by date
    sr = [v for v in enumerate(res)]
    sr.sort(key=lambda e: (to_date(e[1][4]).timestamp(), e[0]))
    res = [v[1] for v in sr]
    df = pd.DataFrame(res, columns=entry_cols)
    return df


def f_name(check, f1, f2):
    if check:
        return f1
    return f2


# loads data from Bank_Statement_Lines
# returns Entries list
def load_lines(file_name):
    logger.info("loading entry lines {}".format(file_name))
    df = pd.read_csv(file_name, sep=',')
    logger.info("loaded entry lines {} rows".format(len(df)))
    logger.debug("{}".format(df.head(n=10)))
    hd = list(df)
    logger.info("Headers: {}".format(hd))
    res = []
    found = set()
    data = df.to_dict('records')

    for d in data:
        ext_id = e_str(d['External_Document_No_'])
        if ext_id in found:
            continue
        found.add(ext_id)
        credit = PaymentType.from_s(d['N_CdtDbtInd']) == PaymentType.CRDT
        values = [d[f_name(not credit, "N_ND_TD_RP_Cdtr_Nm", "N_ND_TD_RP_Dbtr_Nm")],
                  d["N_ND_TD_RmtInf_Ustrd"], d['N_CdtDbtInd'],
                  e_float(d['N_Amt']), d['N_BookDt_Dt'], iban(d),
                  d['N_ND_TD_Refs_EndToEndId'],
                  "", "",
                  e_currency(d['Acct_Ccy']),
                  "",
                  d['External_Document_No_'], '', d['Bank_Account_No_']]
        res.append(Entry({key: value for key, value in zip(entry_cols, values)}))
    # stable sort by date
    sr = [v for v in enumerate(res)]
    sr.sort(key=lambda e: (e[1].date, e[0]))
    res = [v[1] for v in sr]
    return res
