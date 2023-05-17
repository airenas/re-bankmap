class PredictionCfg:
    def __init__(self, company="", limit=1.5, top_best=2, next_train=None):
        self.limit = limit
        self.tops = top_best
        self.company = company
        self.next_train = next_train

    @classmethod
    def default(cls, company):
        return PredictionCfg(company=company)

    @classmethod
    def from_dict(cls, param):
        return PredictionCfg(**param)
