## Duomenys

Bank Statement Entries

- 4213
- 3803 atpažinta prieš tai 
- 410 neatpažinta, iš jų 61 nauji, nėra į ką atpažinti


Customer Entries 
Vendor Entries
Bank Accounts
GL Accounts

## Optimizavimo uždavinys

Kiekvienam `Bank Statement Entry` suskaičiuojame atstumą tarp kiekvieno `Customer Entries`, `Vendor Entries`, `Bank Accounts`, `GL Accounts` įrašo. Parenkam geriausią Customer, Vendor, BA, GLA.

Kriterijai:
1) `cust.name == entr.desc` - [0,1]
2) vardo panašumas `cust.name vs entry.desc` - bag-of-words similarity + jaro_winkler [0-1]
3) `cust.iban == entry.iban` - [0,1]
4) entry.msg contains cust.ext_doc_no - [0,1]
5) ar buvo toks mokėjimas praeityje [0,1] 
    yra `cust.no = entryprev.rec_no`, kur `entryprev.desc = entry.desc && entryprev.iban == entry.iban && entry.date > entryprev.date`

    sprendžia
    BankAccounts
    TextToAccountMapping
-
6) `cust.date - entry.date`
7) `cust.duedate - entry.date`
8) `cust.amount - entry.ammount`


9) `currency code` pajungti

## Results

Acc not empty    : 0.977 (94/4102)

su atpažinimo slenksčiu
Acc w/o rejected : 0.990 (40/4048)


