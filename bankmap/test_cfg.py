from bankmap.cfg import PredictionCfg


def test_from_dict():
    assert PredictionCfg.from_dict({"version": 10}).version == 10
    assert PredictionCfg.from_dict({"tune_count": 10}).version == 0
    assert PredictionCfg.from_dict({}).skip_older_than_days == 60
    assert PredictionCfg.from_dict({"skip_older_than_days": 10}).skip_older_than_days == 10
    assert PredictionCfg.from_dict({}).timeout_sec == 3600
    assert PredictionCfg.from_dict({"timeout_sec": 10}).timeout_sec == 10
