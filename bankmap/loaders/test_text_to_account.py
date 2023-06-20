import pandas as pd

from bankmap.data import LType
from bankmap.loaders.text_to_account import load_text_to_accounts_df


def test_empty():
    assert load_text_to_accounts_df(pd.DataFrame([], columns=['Mapping_Text', 'Bal__Source_Type', 'Bal__Source_No_',
                                                              'Credit_Acc__No_', 'Debit_Acc__No_'])) == []


def test_simple():
    maps = load_text_to_accounts_df(pd.DataFrame([["olia", "G/L Account", "12", "", ""]],
                                                 columns=['Mapping_Text', 'Bal__Source_Type', 'Bal__Source_No_',
                                                          'Credit_Acc__No_', 'Debit_Acc__No_']))
    assert len(maps) == 1
    assert maps[0].text == "olia"
    assert maps[0].type == LType.GL
    assert maps[0].account == "12"
    assert maps[0].debit_account == ""
    assert maps[0].credit_account == ""


def test_credit():
    maps = load_text_to_accounts_df(pd.DataFrame([["olia", "G/L Account", "12", "10", "11"]],
                                                 columns=['Mapping_Text', 'Bal__Source_Type', 'Bal__Source_No_',
                                                          'Credit_Acc__No_', 'Debit_Acc__No_']))
    assert len(maps) == 1
    assert maps[0].text == "olia"
    assert maps[0].type == LType.GL
    assert maps[0].account == "12"
    assert maps[0].credit_account == "10"
    assert maps[0].debit_account == "11"


def test_sort():
    maps = load_text_to_accounts_df(pd.DataFrame(
        [["olia", "G/L Account", "12", "10", "11"], ["olia 2", "G/L Account", "12", "10", "11"],
         ["o2", "G/L Account", "12", "10", "11"]],
        columns=['Mapping_Text', 'Bal__Source_Type', 'Bal__Source_No_',
                 'Credit_Acc__No_', 'Debit_Acc__No_']))
    assert len(maps) == 3
    assert maps[0].text == "olia 2"
    assert maps[1].text == "olia"
    assert maps[2].text == "o2"
