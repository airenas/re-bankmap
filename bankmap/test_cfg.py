from bankmap.cfg import PredictionCfg


def test_from_dict():
    assert PredictionCfg.from_dict({"version": 10}).version == 10
    assert PredictionCfg.from_dict({"tune_count": 10}).version == 0
