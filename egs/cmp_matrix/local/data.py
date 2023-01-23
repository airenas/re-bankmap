import math
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict

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
        self.doc_ids = e_str(row['Docs'])

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
        if s == "Grąž. paž." or s == "Grąžinimo pažyma" or s == "Grąžinimas":
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
        return "{} - {}:{} - {}, {}, {}, {}, {}".format(self.type, self.id, self.doc_no, self.name, self.doc_date,
                                                        self.ext_doc,
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


class Arena:
    def __init__(self, l_entries, apps):
        self.l_entries = l_entries
        self.gl_entries: List[LEntry] = [l for l in filter(lambda x: x.type in [LType.GL, LType.BA], l_entries)]
        self.entries = [l for l in filter(lambda x: x.type in [LType.CUST, LType.VEND], l_entries)]
        self.apps = apps
        self.date = None
        logger.info("GL, BA count: {}".format(len(self.gl_entries)))
        logger.info("L count     : {}".format(len(self.entries)))
        logger.info("Apps count  : {}".format(len(self.apps)))
        self.entries.sort(key=lambda e: e.doc_date.timestamp() if e.doc_date else 1)
        self.apps.sort(key=lambda e: e.apply_date.timestamp() if e.apply_date else 1)
        self.date = self.entries[0].doc_date - timedelta(days=1)
        self.playground: Dict[str, LEntry] = {}
        self.from_entry, self.from_apps = 0, 0
        logger.info("Start date  : {}".format(self.date))
        self.cust_filter = ""
        self.doc_filter = ""

    def move(self, dt):
        if self.date < dt:
            while self.date < dt:
                ndt = self.date + timedelta(days=1)
                logger.debug("Move to date  : {}".format(ndt))
                while self.from_entry < len(self.entries):
                    entry = self.entries[self.from_entry]
                    if entry.doc_date > ndt:
                        break
                    if self.doc_filter:
                        if self.doc_filter == entry.doc_no:
                            logger.info("Add  : {} {}".format(entry.doc_no, entry.to_str()))
                    elif self.cust_filter:
                        if self.cust_filter == entry.id:
                            logger.info("Add  : {} {}".format(entry.doc_no, entry.to_str()))
                    else:
                        logger.debug("Add  : {} {}".format(entry.doc_no, entry.to_str()))
                    self.playground[entry.doc_no] = entry
                    self.from_entry += 1
                while self.from_apps < len(self.apps):
                    app = self.apps[self.from_apps]
                    if app.apply_date >= ndt:
                        break
                    entry = self.playground.get(app.doc_no, None)
                    if entry is not None:
                        if math.isclose(app.remaining, 0):
                            if self.doc_filter:
                                if self.doc_filter == app.doc_no:
                                    logger.info("Drop: {} {}".format(entry.doc_no, entry.to_str()))
                            elif self.cust_filter:
                                if self.cust_filter == app.cv_no:
                                    logger.info("Drop: {} {}".format(entry.doc_no, entry.to_str()))
                            else:
                                logger.debug("Drop: {} {}".format(entry.doc_no, entry.to_str()))
                            del self.playground[app.doc_no]
                        else:
                            if self.cust_filter:
                                if self.cust_filter == app.cv_no:
                                    logger.info(
                                        "Change amount {}: from {} to {}".format(app.doc_no, entry.amount,
                                                                                 app.remaining))
                            else:
                                logger.debug(
                                    "Change amount {}: from {} to {}".format(app.doc_no, entry.amount, app.remaining))
                            entry.amount = app.remaining
                    else:
                        if self.doc_filter:
                            if self.doc_filter == app.doc_no:
                                logger.info("Not found {}: {}".format(app.doc_no, app.to_str()))
                                changed = True
                        elif self.cust_filter:
                            if self.cust_filter == app.cv_no:
                                logger.info("Not found {}: {}".format(app.doc_no, app.to_str()))
                        else:
                            logger.debug("Not found {}: {}".format(app.doc_no, app.to_str()))
                    self.from_apps += 1
                self.date = ndt
                if self.date > dt:
                    self.date = dt
            logger.info("Items to compare : {}".format(len(self.playground)))
            if self.cust_filter:
                ad = [x for x in self.playground.values() if x.id == self.cust_filter]
                logger.info("Active docs ({}):".format(len(ad)))
                for e in ad:
                    logger.info("{}".format(e.to_str()))
        else:
            logger.debug("Up to date  : {}".format(dt))

    def add_cust(self, c):
        self.cust_filter = c

    def add_doc(self, doc):
        self.doc_filter = doc
