import math
from datetime import datetime
from enum import Enum

from src.utils.logger import logger


class App:
    def __init__(self, row):
        self.type = LType.from_s(e_str(row['Type']))
        self.doc_no = e_str(row['Document_No'])
        self.entry_no = e_str(row['Entry_No'])
        self.apply_date = to_date(row['Apply_Date'])
        self.amount = e_float(row['Apply_Amount'])
        self.remaining = e_float(row['Remaining_Amount'])
        self.cv_no = e_str(row['CV_No'])
        self.cv_name = e_str(row['CV_Name'])

    def to_str(self):
        return "{} - {} - {} ({})[{}:{}]".format(self.type, self.apply_date, self.amount,
                                                 math.isclose(self.remaining, 0), self.cv_no, self.cv_name)


class Entry:
    def __init__(self, row):
        self.who = e_str(row['Description'])
        self.iban = e_str(row['IBAN'])
        self.msg = e_str(row['Message'])
        self.date = datetime.fromisoformat(row['Date'])
        self.amount = e_float(row['Amount'])
        self.rec_id = e_str(row['RecAccount'])
        self.doc_id = e_str(row['RecDoc'])
        self.recognized = row['Recognized']
        self.currency = row['Currency']
        self.type = PaymentType.from_s(e_str(row['CdtDbtInd']))

    def to_str(self):
        return "{} - {} - {}".format(self.who, self.msg, self.date)


def to_date(p):
    try:
        return None if p != p else datetime.fromisoformat(p)
    except BaseException as err:
        logger.info("{}".format(p))
        raise err


class PaymentType(Enum):
    DBIT = 1
    CRDT = 2

    @staticmethod
    def from_s(s):
        if s == "CRDT":
            return PaymentType.CRDT
        if s == "DBIT":
            return PaymentType.DBIT
        raise Exception("Unknown doc type '{}'".format(s))


class DocType(Enum):
    SF = 1
    GRAZ_PAZ = 2
    GL = 3
    BA = 4

    @staticmethod
    def from_s(s):
        if s == "SF":
            return DocType.SF
        if s == "Grąž. paž.":
            return DocType.GRAZ_PAZ
        if s == "GL":
            return DocType.GL
        if s == "BA":
            return DocType.BA
        raise Exception("Unknown doc type '{}'".format(s))


class LType(Enum):
    CUST = 1
    VEND = 2
    GL = 3
    BA = 4

    @staticmethod
    def from_s(s):
        if s == "Customer":
            return LType.CUST
        if s == "Vendor":
            return LType.VEND
        if s == "GL":
            return LType.GL
        if s == "BA":
            return LType.BA
        raise Exception("Unknown type {}".format(s))


class LEntry:
    def __init__(self, row):
        try:
            self.type = LType.from_s(e_str(row['Type']))
            self.id = e_str(row['No'])
            self.name = e_str(row['Name'])
            self.iban = e_str(row['IBAN'])
            self.ext_doc = e_str(row['ExtDoc'])
            self.doc_no = e_str(row['Document_No'])
            self.due_date = to_date(row['Due_Date'])
            self.doc_date = to_date(row['Document_Date'])
            self.amount = e_float(row['Amount'])
            self.currency = row['Currency']
            self.doc_type = DocType.from_s(e_str(row['Document_Type']))
        except BaseException as err:
            raise Exception("Err: {}: for {}".format(err, row))

    def to_str(self):
        return "{} - {} - {}, {}, {}, {}, {}".format(self.type, self.id, self.name, self.doc_date, self.ext_doc,
                                                     self.doc_type, self.amount)


def e_str(p):
    if p != p:
        return ''
    return str(p).strip()


def e_float(p):
    if p != p:
        return 0
    return float(e_str(p).replace(",", "."))


def e_currency(p):
    if p != p:
        return "EUR"
    return e_str(p).upper()
