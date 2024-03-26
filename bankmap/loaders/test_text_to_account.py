from bankmap.data import LType
from bankmap.loaders.text_to_account import read_text_to_accounts


def test_simple():
    maps = read_text_to_accounts([{'mappingText': 'olia', 'debitAccountNumber': '',
                                   'creditAccountNumber': '', 'balSourceType': 'G/L Account', 'balSourceNumber': '12'}],
                                 "t.jsonl")
    assert len(maps) == 1
    assert maps[0].text == "olia"
    assert maps[0].type == LType.GL
    assert maps[0].account == "12"
    assert maps[0].debit_account == ""
    assert maps[0].credit_account == ""


def test_credit():
    maps = read_text_to_accounts([{'mappingText': 'olia', 'debitAccountNumber': '11',
                                   'creditAccountNumber': '10', 'balSourceType': 'G/L Account',
                                   'balSourceNumber': '12'}],
                                 "t.jsonl")
    assert len(maps) == 1
    assert maps[0].text == "olia"
    assert maps[0].type == LType.GL
    assert maps[0].account == "12"
    assert maps[0].credit_account == "10"
    assert maps[0].debit_account == "11"


def test_sort():
    maps = read_text_to_accounts(
        [{'mappingText': 'olia', 'debitAccountNumber': '11',
          'creditAccountNumber': '10', 'balSourceType': 'G/L Account',
          'balSourceNumber': '12'},
         {'mappingText': 'olia 2', 'debitAccountNumber': '11',
          'creditAccountNumber': '10', 'balSourceType': 'G/L Account',
          'balSourceNumber': '12'},
         {'mappingText': 'o2', 'debitAccountNumber': '11',
          'creditAccountNumber': '10', 'balSourceType': 'G/L Account',
          'balSourceNumber': '12'}
         ],
        "t.jsonl")
    assert len(maps) == 3
    assert maps[0].text == "olia 2"
    assert maps[1].text == "olia"
    assert maps[2].text == "o2"
