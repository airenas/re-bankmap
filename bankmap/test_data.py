import datetime

import pytest

from bankmap.data import to_date, LType


def test_to_date():
    # assert to_date("11/10/2022 12:00:00 AM") == datetime.datetime(2022, 11, 10, 0, 0)
    # assert to_date("11/10/2022 12:00:00 PM") == datetime.datetime(2022, 11, 10, 12, 0)
    assert to_date("2022-11-10 00:00:00") == datetime.datetime(2022, 11, 10, 0, 0)
    assert to_date("2022-11-10 00:00:00.000") == datetime.datetime(2022, 11, 10, 0, 0)
    assert to_date(None) is None
    assert to_date("") is None
    with pytest.raises(Exception):
        to_date("1980-11-10 00:00:00.000")
    with pytest.raises(Exception):
        to_date("2100-11-10 00:00:00.000")


def test_ltype_supported():
    assert not LType.supported("Employee")
    assert not LType.supported("")

    assert LType.supported("Customer")
    assert LType.supported("Vendor")
    assert LType.supported("G/L Account")
    assert LType.supported("Bank Account")
