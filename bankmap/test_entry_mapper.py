from bankmap.cfg import PredictionCfg, recommended_confidence
from bankmap.data import LType
from bankmap.entry_mapper import get_confidence, calc_confidence


def test_get_confidence():
    assert get_confidence(1.2, LType.CUST, PredictionCfg(limit=1.5)) == 0.5
    assert get_confidence(1.512, LType.CUST, PredictionCfg(limit=1.5)) == recommended_confidence
    assert get_confidence(1.512, LType.CUST,
                          PredictionCfg(limit=1.5, limits={"Customer": {"1": 1.6, "0.995": 1.5, "0.95": 1.0}})) == 0.995
    assert get_confidence(1.512,  LType.VEND,
                          PredictionCfg(limit=1.5, limits={"Customer": {"1": 1.6, "0.995": 1.5, "0.95": 1.0},
                                                           "all": {"1": 1.6, "0.995": 1.55, "0.95": 0.9}})) == 0.95
    assert get_confidence(1.2, LType.CUST,
                          PredictionCfg(limit=1.5, limits={"Customer": {"1": 1.6, "0.995": 1.5, "0.95": 1.0},
                                                           "all": {"1": 1.5, "0.995": 1.4, "0.95": 0.9}})) == 0.95
    assert get_confidence(0.8, LType.CUST,
                          PredictionCfg(limit=1.5, limits={"Customer": {"1": 1.6, "0.995": 1.5, "0.95": 1.0},
                                                           "all": {"1": 1.5, "0.995": 1.4, "0.95": 0.9}})) == 0.5
    assert get_confidence(1.512, LType.CUST,
                          PredictionCfg(limit=1.5, limits={"Customer": {},
                                                           "all": {"1": 1.6, "0.995": 1.55, "0.9": 0.9}})) == 0.9


def test_calc_confidence():
    assert calc_confidence(1.2, {"1": 1.6, "0.995": 1.5, "0.95": 1.0}) == 0.95
    assert calc_confidence(1.0, {"1": 1.6, "0.995": 1.5, "0.95": 1.01}) == 0.5
    assert calc_confidence(1.5, {"1": 1.6, "0.995": 1.5, "0.95": 1.01}) == 0.995
