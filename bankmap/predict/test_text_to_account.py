import pandas as pd

from bankmap.data import Entry, PaymentType, TextToAccountMap
from bankmap.loaders.text_to_account import load_text_to_accounts_df
from bankmap.predict.text_to_account import map_text_to_account, matches_text, map_account


def test_complete():
    entry = Entry({"BankAccount": "", 'DocNo': "", 'Description': "",
                   'IBAN': "", 'Message': "oliaa", 'Date': "", 'Amount': 10, 'RecAccount': "", 'Currency': "",
                   'CdtDbtInd': "DBIT", 'RecDocs': "", 'RecType': ""})
    maps = load_text_to_accounts_df(pd.DataFrame([["volia", "G/L Account", "12", "", ""],
                                                  ["olia olia", "G/L Account", "12", "10", "11"]],
                                                 columns=['Mapping_Text', 'Bal__Source_Type', 'Bal__Source_No_',
                                                          'Credit_Acc__No_', 'Debit_Acc__No_']))
    res = map_text_to_account(entry, maps)
    assert res is None
    entry.msg = "volia"
    res = map_text_to_account(entry, maps)
    assert res.account == "12"
    entry.msg = "olia olia aaa"
    res = map_text_to_account(entry, maps)
    assert res.account == "11"
    entry.type = PaymentType.CRDT
    res = map_text_to_account(entry, maps)
    assert res.account == "10"


def test_matches_text():
    assert matches_text("aaa", "aaa")
    assert matches_text("aaa aaa", "aaa aaa")
    assert matches_text("vikas-aaa 1245", "vikas-aaa")
    assert matches_text("Aš vikas-aaa 1245", "aš vikas-aaa")
    assert matches_text("aaa,", "aaa") is False


def test_map_account():
    assert map_account(TextToAccountMap({'Type': 'G/L Account', 'Text': 'Olia', 'Account': "common",
                                         'Credit_Account': "crdt", 'Debit_Account': "dbit"}),
                       PaymentType.CRDT) == "crdt"
    assert map_account(TextToAccountMap({'Type': 'G/L Account', 'Text': 'Olia', 'Account': "common",
                                         'Credit_Account': "crdt", 'Debit_Account': "dbit"}),
                       PaymentType.DBIT) == "dbit"
    assert map_account(TextToAccountMap({'Type': 'G/L Account', 'Text': 'Olia', 'Account': "common",
                                         'Credit_Account': "", 'Debit_Account': "dbit"}),
                       PaymentType.CRDT) == "common"
    assert map_account(TextToAccountMap({'Type': 'Vendor', 'Text': 'Olia', 'Account': "common",
                                         'Credit_Account': "crdt", 'Debit_Account': "dbit"}),
                       PaymentType.CRDT) == "common"
    assert map_account(TextToAccountMap({'Type': 'G/L Account', 'Text': 'Olia', 'Account': "common",
                                         'Credit_Account': "crdt", 'Debit_Account': ""}),
                       PaymentType.DBIT) == "common"
