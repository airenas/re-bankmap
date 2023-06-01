import datetime

from bankmap.utils.utils import str_date, empty_if_n


def test_str_date():
    assert str_date(None) == ""
    assert str_date(
        datetime.datetime(year=2023, month=1, day=10, hour=1, minute=15, microsecond=501)) == "2023-01-10T01:15:00"


def test_empty_if_n():
    assert empty_if_n(None) == ""
    assert empty_if_n(10) == 10
    assert empty_if_n("10") == "10"
