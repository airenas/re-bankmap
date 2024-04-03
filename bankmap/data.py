import datetime
from datetime import timedelta
from enum import Enum
from typing import List, Dict

from dateutil.parser import parser

from bankmap.logger import logger
from bankmap.similarity.similarity import num_close

time_parser = parser()

check_date_max = datetime.datetime.today() + timedelta(days=20 * 365)
check_date_min = datetime.datetime.today() - timedelta(days=40 * 365)


class Ctx:
    def __init__(self, history_days: int = None, stats=None):
        self.name_sim_cache = {}
        self.history = timedelta(days=history_days) if history_days is not None else None
        self.stats = stats


class App:
    def __init__(self, row):
        self.type = LType.from_s(row['type'])
        self.doc_no = row['document_number']
        self.apply_date = to_date(row['apply_date'])
        self.amount = row['apply_amount']
        self.remaining = row['remaining_amount']
        self.cv_no = row['cv_number']

    def to_str(self):
        return "{} - {} - {} ({})[{}:{}]".format(self.type, self.apply_date, self.amount,
                                                 num_close(self.remaining, 0), "", "")


class PaymentType(Enum):
    DBIT = 1
    CRDT = 2

    @staticmethod
    def from_s(s):
        if s == "CRDT" or s == "Credit":
            return PaymentType.CRDT
        if s == "DBIT" or s == "Debit":
            return PaymentType.DBIT
        raise Exception("Unknown doc type '{}'".format(s))

    def to_s(self):
        if self == PaymentType.CRDT:
            return "Credit"
        if self == PaymentType.DBIT:
            return "Debit"
        raise Exception("Unknown payment type '{}'".format(self))


class Recognition:
    def __init__(self, _type, no):
        self.no = no
        self.type = LType.from_s(_type)


class Entry:
    def __init__(self, row):
        self.bank_account = e_str(row['bankAccount'])
        self.ext_id = row['externalDocumentNumber']
        self.who = e_str(row['description'])
        self.iban = e_str(row['iban'])
        self.msg = e_str(row['message'])
        self.date = to_date(row['date'])
        self.amount = row['amount']
        self.rec_id = e_str(row['recAccount'])
        self.currency = row['currency']
        self.type = PaymentType.from_s(row['transactionType'])
        self.doc_ids = e_str(row['recDocs'])
        self.rec_type = LType.from_s(row['recType'])
        self.msg_clean = ''.join('#' if char.isdigit() else char for char in self.msg)
        self.e2e_id = e_str_e(row, 'e2eId')

    def to_str(self):
        return "{} - {} - {}".format(self.who, self.msg, self.date)


def to_date(p):
    try:
        if p is None or p == '':
            return None
        if isinstance(p, datetime.datetime):
            return p
        res = datetime.datetime.fromisoformat(p)
        res = res.replace(tzinfo=None)
        if res > check_date_max or res < check_date_min:
            raise Exception(f"Wrong date '{p}'")
        return res
    except BaseException as err:
        logger.error("date:'{}'".format(p))
        raise err


class MapType(Enum):
    UNUSED = 0
    MANUAL = 1
    OLDEST = 2

    @staticmethod
    def from_s(s):
        if s == "Rankiniu būdu" or s == "ManualMap" or s == "Manual":
            return MapType.MANUAL
        if s == "Sugretinti su seniausiu" or s == "OldestMap" or s == "Apply to Oldest":
            return MapType.OLDEST
        if s == "Unused" or s == '':
            return MapType.UNUSED
        raise Exception("Unknown map type '{}'".format(s))

    def to_s(self):
        if self == MapType.MANUAL:
            return "ManualMap"
        if self == MapType.OLDEST:
            return "OldestMap"
        if self == MapType.UNUSED:
            return "Unused"
        raise Exception("Unknown map type '{}'".format(self))


class DocType(Enum):
    SF = 1
    GRAZ_PAZ = 2
    GL = 3
    BA = 4

    @staticmethod
    def from_s(s):
        if s == "Delspinigių pažyma" or s == "Invoice" or s == "SF" or s == "Finance Charge Memo":
            return DocType.SF
        if s == "Grąž. paž." or s == "Grąžinimo pažyma" or s == "Grąžinimas" or s == "Credit Memo" or s == "Refund":
            return DocType.GRAZ_PAZ
        if s == "G/L Account":
            return DocType.GL
        if s == "Bank Account":
            return DocType.BA
        raise Exception("Unknown doc type '{}'".format(s))

    @staticmethod
    def skip(s):
        return (s == "Mokėjimas" or s == "Payment" or s == "Reminder" or s == "Bill" or s == "Prepayment"
                or s == "Prepayment Refund")

    def to_s(self):
        if self == DocType.SF:
            return "Invoice"
        if self == DocType.GRAZ_PAZ:
            return "Credit Memo"
        if self == DocType.GL:
            return "G/L Account"
        if self == DocType.BA:
            return "Bank Account"
        raise Exception("Unknown doc type '{}'".format(self))


class LType(Enum):
    CUST = 1
    VEND = 2
    GL = 3
    BA = 4
    UNSET = 5

    @staticmethod
    def from_s(s):
        if s == "Customer" or s == "Pirkėjas":
            return LType.CUST
        if s == "Vendor" or s == "Tiekėjas":
            return LType.VEND
        if s == "G/L Account" or s == "DK sąskaita":
            return LType.GL
        if s == "Bank Account" or s == "Banko sąskaita":
            return LType.BA
        if s == "":
            return LType.UNSET
        raise Exception("Unknown type {}".format(s))

    @staticmethod
    def supported(s):
        return s == "Customer" or s == "Vendor" or s == "G/L Account" or s == "Bank Account"

    def to_s(self):
        if self == LType.CUST:
            return "Customer"
        if self == LType.VEND:
            return "Vendor"
        if self == LType.GL:
            return "G/L Account"
        if self == LType.BA:
            return "Bank Account"
        if self == LType.UNSET:
            return ""
        raise Exception("Unknown l type '{}'".format(self))


class LEntry:
    def __init__(self, row):
        try:
            self.type = LType.from_s(e_str(row['type']))
            self.id = e_str(row['number'])  # vendor/cust/gl/ba
            self.name = e_str(row['name'])
            self.iban = e_str(row['iban'])
            self.ext_doc = e_str(row['externalDocumentNumber'])
            self.doc_no = e_str(row['documentNumber'])
            self.doc_date = to_date(row['documentDate'])
            try:
                self.due_date = to_date(row['dueDate'])
            except BaseException as err:
                logger.warn("no due date: err: {}".format(err))
                self.due_date = self.doc_date
            self.amount = row['amount']
            self.currency = row['currencyCode']
            self.doc_type = DocType.from_s(row['documentType'])
            self.closed_date = to_date(row['closedAtDate'])
            self.map_type = MapType.from_s(row['mapType'])
            self.open = e_str(row['open']) == 'True'
            self.remaining_amount = e_float(row, 'remainingAmount')
        except BaseException as err:
            raise Exception("Err: {}: for {}".format(err, row))

    def to_str(self):
        return "{} - {}:{} - {}, {}[due {}], {}, {}, {}, {}".format(self.type, self.id, self.doc_no, self.name,
                                                                    self.doc_date, self.due_date,
                                                                    self.ext_doc,
                                                                    self.doc_type, self.amount, self.map_type.to_s())


class TextToAccount:
    def __init__(self, _type, account):
        self.type = _type
        self.account = account


class TextToAccountMap:
    def __init__(self, type_v, text, account, credit_account, debit_account):
        self.type = type_v
        self.text = text
        self.account = account
        self.credit_account = credit_account
        self.debit_account = debit_account


def e_str(p):
    if p is None:
        return ''
    return str(p).strip()


def e_str_e(d, name):
    res = d.get(name)
    if res is None:
        return ''
    return str(res).strip()


def e_str_ne(d, name):
    res = e_str(d.get(name))
    if res == '':
        raise Exception(f"Empty {name}")
    return res


def e_float(d, name):
    p = d.get(name)
    if p is None:
        return 0
    return float(p)


def e_date_ne(d, name):
    res = e_str_ne(d, name)
    return to_date(res)


def e_date(d, name):
    res = e_str_e(d, name)
    if not res:
        return None
    return to_date(res)


def e_currency(p):
    if p is None:
        return "EUR"
    return e_str(p).upper()


class PredictData:
    def __init__(self, gl_ba, sfs, historical_entries, text_to_account_map=None):
        self.gl_ba = gl_ba
        self.sfs = sfs
        self.historical_entries = historical_entries
        self.text_to_account_map = text_to_account_map


class Arena:
    def __init__(self, l_entries, apps):
        self.l_entries = l_entries
        self.gl_entries: List[LEntry] = [e for e in filter(lambda x: x.type in [LType.GL, LType.BA], l_entries)]
        self.entries = [e for e in filter(lambda x: x.type in [LType.CUST, LType.VEND], l_entries)]
        self.apps = apps
        self.date = None
        logger.info("GL, BA count: {}".format(len(self.gl_entries)))
        logger.info("L count     : {}".format(len(self.entries)))
        logger.info("Apps count  : {}".format(len(self.apps)))
        self.entries.sort(key=lambda e: e.doc_date.timestamp() if e.doc_date else 1)
        self.apps.sort(key=lambda e: e.apply_date.timestamp() if e.apply_date else 1)
        if len(self.entries) > 0:
            self.date = self.entries[0].doc_date - timedelta(days=1)
        self.playground: Dict[str, LEntry] = {}
        self.from_entry, self.from_apps = 0, 0
        logger.debug("Start date  : {}".format(self.date))
        self.cust_filter = ""
        self.doc_filter = ""
        self.drop_not_found = dict()

    # flake8: noqa: C901
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
                            logger.debug("Add  : {} {}".format(entry.doc_no, entry.to_str()))
                    elif self.cust_filter:
                        if self.cust_filter == entry.id:
                            logger.debug("Add  : {} {}".format(entry.doc_no, entry.to_str()))
                    else:
                        logger.debug("Add  : {} {}".format(entry.doc_no, entry.to_str()))
                    self.playground[entry.doc_no] = entry
                    self.from_entry += 1
                    # if self.drop_not_found.get(entry.doc_no) == 1:
                    #     logger.warn("Add {}, but wanted to drop before".format(entry.doc_no))
                while self.from_apps < len(self.apps):
                    app = self.apps[self.from_apps]
                    if app.apply_date >= ndt:
                        break
                    entry = self.playground.get(app.doc_no, None)
                    if entry is not None:
                        remaining = self.remaining(entry.amount, app.amount)
                        if num_close(remaining, 0):
                            if self.doc_filter:
                                if self.doc_filter == app.doc_no:
                                    logger.debug("Drop: {} {}".format(entry.doc_no, entry.to_str()))
                            elif self.cust_filter:
                                if self.cust_filter == app.cv_no:
                                    logger.debug("Drop: {} {}".format(entry.doc_no, entry.to_str()))
                            else:
                                logger.debug("Drop: {} {}".format(entry.doc_no, entry.to_str()))
                            del self.playground[app.doc_no]
                        else:
                            if self.cust_filter:
                                if self.cust_filter == app.cv_no:
                                    logger.info(
                                        "Change amount {}: from {} to {}".format(app.doc_no, entry.amount, remaining))
                            else:
                                logger.debug(
                                    "Change amount {}: from {} to {}".format(app.doc_no, entry.amount, remaining))
                            entry.amount = remaining
                    else:
                        if self.doc_filter:
                            if self.doc_filter == app.doc_no:
                                logger.debug("Not found {}: {}".format(app.doc_no, app.to_str()))
                        elif self.cust_filter:
                            if self.cust_filter == app.cv_no:
                                logger.debug("Not found {}: {}".format(app.doc_no, app.to_str()))
                        else:
                            logger.debug("Not found {}: {}".format(app.doc_no, app.to_str()))
                        self.drop_not_found[app.doc_no] = 1
                    self.from_apps += 1
                # for e in list(self.playground.values()):
                #     if e.closed_date and e.closed_date < ndt:
                #         logger.debug("Drop by closed date value: {} {}, {}".format(e.closed_date, e.doc_no, e.to_str()))
                #         del self.playground[e.doc_no]
                self.date = ndt
                if self.date > dt:
                    self.date = dt
            logger.debug("Items to compare : {} at {}".format(len(self.playground), self.date))
            if self.cust_filter:
                ad = [x for x in self.playground.values() if x.id == self.cust_filter]
                logger.info("\n\n=============================")
                logger.info("Active docs ({}):".format(len(ad)))
                for e in ad:
                    logger.info("{}".format(e.to_str()))
        else:
            logger.debug("Up to date  : {}".format(dt))

    def add_cust(self, c):
        self.cust_filter = c

    def add_doc(self, doc):
        self.doc_filter = doc

    def remaining(self, amount, value):
        if amount >= 0:
            res = amount - abs(value)
        else:
            res = amount + abs(value)
        if (amount >= 0 > res or amount <= 0 < res) and not num_close(res, 0):
            logger.debug("Amount change from {} to {}".format(amount, res))
            res = 0
        return res
