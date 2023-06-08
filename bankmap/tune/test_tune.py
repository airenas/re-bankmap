from bankmap.tune.tune import calc_limits, Cmp


def make_cmps(v, cor, count):
    res = []
    for i in range(count):
        res.append(Cmp(correct=cor, value=v, _type="any"))
    return res


def test_calc_limits():
    assert calc_limits(
        make_cmps(1.2, True, 10) + make_cmps(1.1, False, 1) + make_cmps(1.0, True, 1000) + make_cmps(0.9, False, 1),
        [1, 0.995, 0.9]) == {1: 1.2, 0.9: 1.1}
