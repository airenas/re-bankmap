from bankmap.cfg import default_limit_value, recommended_confidence


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


def get_bar_def_value(v):
    if v > recommended_confidence:
        return default_limit_value + 1
    return default_limit_value


def calc_limits(cmps, bars):
    res = {}
    if len(cmps) == 0:
        res = {v: get_bar_def_value(v) for v in bars}
    err, count = 0, 0
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
