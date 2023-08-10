from bankmap.loaders.entries import non_empty_str


def test_non_empty_str():
    assert non_empty_str("11/10/2022 12:00:00 AM", "2") == "11/10/2022 12:00:00 AM"
    assert non_empty_str("", "2") == "2"
    assert non_empty_str("0", "2") == "2"
    assert non_empty_str("1", "2") == "1"
