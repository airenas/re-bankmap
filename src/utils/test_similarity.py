from datetime import datetime

from src.utils.similarity import name_sim, date_sim, num_sim


def test_str_sim():
    assert name_sim("", "oliaa, uab") == 0
    assert name_sim("oliaa, uab", "") == 0
    assert name_sim("uab olia", "olia, uab") > 0.7
    assert name_sim("uab olia", "uab mama") < name_sim("uab olia", "olia, uab")
    assert name_sim("uab olia", "mama, uab") < name_sim("uab olia", "oliaa, uab")
    assert name_sim("uab olia", "olia, uab") > name_sim("uab olia", "olia, UAB")
    assert name_sim("uab olia", "oliaa, uab") < name_sim("uab olia", "olia, ab")


def test_date_sim():
    assert date_sim(datetime(2020, 5, 17), datetime(2020, 5, 17)) == 1
    assert date_sim(datetime(2020, 5, 17), datetime(2020, 5, 10)) > 0.5
    assert date_sim(datetime(2020, 5, 17), datetime(2020, 5, 27)) > 0.5
    assert date_sim(datetime(2020, 5, 17), datetime(2020, 5, 1)) < 0.5
    assert date_sim(datetime(2020, 5, 17), datetime(2020, 4, 1)) < .1
    assert date_sim(datetime(2020, 5, 17), datetime(2020, 7, 1)) < .1


def test_num_sim():
    assert num_sim(0) == 1
    assert num_sim(1) > 0.5
    assert num_sim(-1) > 0.5
    assert num_sim(10) < 0.5
    assert num_sim(20) < .1
    assert num_sim(-20) < .1
