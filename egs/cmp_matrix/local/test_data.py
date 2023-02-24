import datetime

from egs.cmp_matrix.local.data import to_date


def test_to_date():
    assert to_date("11/10/2022 12:00:00 AM") == datetime.datetime(2022, 11, 10, 0, 0)
    assert to_date("11/10/2022 12:00:00 PM") == datetime.datetime(2022, 11, 10, 12, 0)
    assert to_date("2022-11-10 00:00:00") == datetime.datetime(2022, 11, 10, 0, 0)
    assert to_date(None) == datetime.datetime(2022, 11, 10, 0, 0)
