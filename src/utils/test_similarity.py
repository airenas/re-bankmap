from src.utils.similarity import name_sim


def test_str_sim():
    assert name_sim("", "oliaa, uab") == 0
    assert name_sim("oliaa, uab", "") == 0
    assert name_sim("uab olia", "olia, uab") > 0.7
    assert name_sim("uab olia", "uab mama") < name_sim("uab olia", "olia, uab")
    assert name_sim("uab olia", "mama, uab") < name_sim("uab olia", "oliaa, uab")
    assert name_sim("uab olia", "olia, uab") > name_sim("uab olia", "olia, UAB")
    assert name_sim("uab olia", "oliaa, uab") < name_sim("uab olia", "olia, ab")
