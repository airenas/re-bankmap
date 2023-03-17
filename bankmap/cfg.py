class PredictionCfg:
    def __init__(self, company="", limit=1.5, top_best=2):
        self.limit = limit
        self.tops = top_best
        self.company = company
