import math
from datetime import datetime

from src.utils.similarity import name_sim, date_sim, num_sim, sf_sim, sf_dist, sf_sim_out


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


def test_sf_dist():
    assert sf_dist("SF012345", "SF012345") == 0
    assert sf_dist("SF012345", "SF0142345") == 1
    assert math.isclose(sf_dist("SF012345", "012345"), .6)
    assert math.isclose(sf_dist("SF012345", "01234"), .9)
    assert math.isclose(sf_dist("SF012345", "0123222"), 2.4)


def test_sf_sim():
    assert sf_sim("SF012345", "123 SF012345") == 1
    assert sf_sim("SF012345", "olia SF0142345") == 0
    assert sf_sim("SF012345", "tata 012345;aaa") == .4
    assert math.isclose(sf_sim("SF012345", "tata 01234;aaa"), .1)
    assert sf_sim("SF012345", "123 sf012345") == 1
    assert sf_sim("SF012345", "tata f012345;aaa") == .7
    assert sf_sim("SF012345", "sf01255+012345") == .4
    assert math.isclose(sf_sim("SF012345", "12345"), .1)
    assert math.isclose(sf_sim("SF012345-1", "SF012345"), .4)


def test_sf_sim_out():
    s, v = sf_sim_out("SF012345", "123 SF012345")
    assert s == 1
    assert v == "SF012345"
    s, v = sf_sim_out("SF012345", "tata f012345;aaa")
    assert s == .7
    assert v == "f012345"
