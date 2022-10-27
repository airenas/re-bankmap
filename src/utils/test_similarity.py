from src.utils.similarity import name_sim


def test_str_sim():
    assert name_sim("uab olia", "olia, uab") > 1
    assert name_sim("uab olia", "uab mama") < name_sim("uab olia", "olia, uab")
    assert name_sim("uab olia", "mama, uab") < name_sim("uab olia", "oliaa, uab")
