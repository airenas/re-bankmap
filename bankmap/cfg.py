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
    def __init__(self, company="", limit=1.5, top_best=2, next_train=None, train_last=2000):
        self.limit = limit
        self.tops = top_best
        self.company = company
        self.next_train: datetime.datetime = get_date(next_train)
        self.train_last = train_last

    @classmethod
    def default(cls, company):
        return PredictionCfg(company=company)

    @classmethod
    def from_dict(cls, param):
        return PredictionCfg(**param)

    def to_dic(self):
        res = {
            "limit": self.limit,
            "top_best": self.tops,
            "company": self.company,
            "train_last": self.train_last,
        }
        if self.next_train:
            res["next_train"] = self.next_train.isoformat()
        return res
