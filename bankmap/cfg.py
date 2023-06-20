import datetime

from bankmap.data import time_parser
from bankmap.logger import logger


def get_date(date):
    if date:
        try:
            return time_parser.parse(date)
        except BaseException as err:
            logger.warn("date:'{}': {}".format(date, str(err)))
    return None


class PredictionCfg:
    def __init__(self, company="", limit=1.5, top_best=2, next_train=None, train_last=2000, limits=None,
                 tune_count=None,
                 tune_date=None,
                 version=0,
                 text_map_limit=2.0):
        self.limit = limit
        self.limits = limits
        self.tops = top_best
        self.company = company
        self.next_train: datetime.datetime = get_date(next_train)
        self.train_last = train_last
        self.tune_count = tune_count
        self.tune_date: datetime.datetime = get_date(tune_date)
        self.version = version
        self.text_map_limit = text_map_limit

    @classmethod
    def default(cls, company):
        return PredictionCfg(company=company)

    @classmethod
    def version(cls):
        return 1

    @classmethod
    def from_dict(cls, param):
        return PredictionCfg(**param)

    def to_dic(self):
        res = {
            "limit": self.limit,
            "limits": self.limits,
            "top_best": self.tops,
            "company": self.company,
            "train_last": self.train_last,
            "tune_count": self.tune_count,
            "version": self.version,
            "text_map_limit": self.text_map_limit,
        }
        if self.next_train:
            res["next_train"] = self.next_train.isoformat()
        if self.tune_date:
            res["tune_date"] = self.tune_date.isoformat()
        return res
