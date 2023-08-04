from datetime import datetime

from deploy.az_f.bankmap.function_app import name_with_timestamp


def test_name_with_timestamp():
    assert name_with_timestamp("olia", datetime(2022, 12, 28, 23, 55, 59)) == "olia_2022-12-28T23:55:59.zip"
    assert name_with_timestamp("olia", datetime(2022, 12, 28, 23, 55, 59, 342380)) == "olia_2022-12-28T23:55:59.zip"
    assert name_with_timestamp("olia", datetime(2022, 12, 28)) == "olia_2022-12-28T00:00:00.zip"
