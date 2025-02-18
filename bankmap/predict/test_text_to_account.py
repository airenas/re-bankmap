from bankmap.data import Entry, PaymentType, TextToAccountMap, LType
from bankmap.loaders.text_to_account import read_text_to_accounts
from bankmap.predict.text_to_account import map_text_to_account, matches_text, map_account


def test_complete():
    entry = Entry({"bankAccount": "SOME", 'externalDocumentNumber': "", 'description': "",
                   'iban': "", 'message': "oliaa", 'date': "", 'amount': 10, 'recAccount': "", 'currency': "",
                   'transactionType': "DBIT", 'recDocs': "", 'recType': ""})
    entry_ba = Entry({"bankAccount": "OTHER-BA", 'externalDocumentNumber': "", 'description': "",
                   'iban': "", 'message': "oliaa", 'date': "", 'amount': 10, 'recAccount': "", 'currency': "",
                   'transactionType': "DBIT", 'recDocs': "", 'recType': ""})
    maps = read_text_to_accounts([{'mappingText': 'volia', 'debitAccountNumber': '',
                                   'creditAccountNumber': '', 'balSourceType': 'G/L Account',
                                   'balSourceNumber': '12'},
                                  {'mappingText': 'olia olia', 'debitAccountNumber': '11',
                                   'creditAccountNumber': '10', 'balSourceType': 'G/L Account',
                                   'balSourceNumber': '12'},
                                  {'mappingText': 'olia olia', 'debitAccountNumber': '11-ba',
                                   'creditAccountNumber': '10-ba', 'balSourceType': 'G/L Account',
                                   'balSourceNumber': '12-ba', 'bankAccountNo': 'OTHER-BA'},
                                  ], "t.jsonl")
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

    entry_ba.msg = "olia olia aaa"
    res = map_text_to_account(entry_ba, maps)
    assert res.account == "11-ba"


def test_matches_text():
    assert matches_text("aaa", "aaa")
    assert matches_text("aaa aaa", "aaa aaa")
    assert matches_text("vikas-aaa 1245", "vikas-aaa")
    assert matches_text("Aš vikas-aaa 1245", "aš vikas-aaa")
    assert matches_text("aaa,", "aaa") is False


def test_map_account():
    assert map_account(TextToAccountMap(type_v=LType.from_s('G/L Account'), text='Olia', account="common",
                                        credit_account="crdt", debit_account="dbit", bank_account=""),
                       PaymentType.CRDT) == "crdt"
    assert map_account(TextToAccountMap(type_v=LType.from_s('G/L Account'), text='Olia', account="common",
                                        credit_account="crdt", debit_account="dbit", bank_account=""),
                       PaymentType.DBIT) == "dbit"
    assert map_account(TextToAccountMap(type_v=LType.from_s('G/L Account'), text='Olia', account="common",
                                        credit_account="", debit_account="dbit", bank_account=""),
                       PaymentType.CRDT) == "common"
    assert map_account(TextToAccountMap(type_v=LType.from_s('Vendor'), text='Olia', account="common",
                                        credit_account="crdt", debit_account="dbit", bank_account=""),
                       PaymentType.CRDT) == "common"
    assert map_account(TextToAccountMap(type_v=LType.from_s('G/L Account'), text='Olia', account="common",
                                        credit_account="crdt", debit_account="", bank_account=""),
                       PaymentType.DBIT) == "common"
