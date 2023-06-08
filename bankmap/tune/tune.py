class Cmp:
    def __init__(self, _type, value, correct):
        self.type = _type
        self.value = value
        self.correct = correct


def fix_probabilities(res, bars):
    pv = 0
    for p in reversed(bars):
        if p in res:
            v = res[p]
            if v < pv:
                del res[p]
            else:
                pv = v
    return res


def calc_limits(cmps, bars):
    res = {}
    if len(cmps) == 0:
        res = {v: 2.5 for v in bars}
    err, count, cop_bars = 0, 0, bars
    for c in cmps:
        count += 1
        if not c.correct:
            err += 1
            v = (count - err) / count
            pv = 1
            for p in bars:
                if pv >= v > p:
                    res[p] = c.value
                    break
                pv = p
        elif err == 0:
            for p in bars:
                if p == 1:
                    res[p] = c.value
                    break
    return fix_probabilities(res, bars)
