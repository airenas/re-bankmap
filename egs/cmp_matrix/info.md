# Demo 5
2023 05 10

Rezultatai: P
```txt
Empty              : 0.537 (1563/3379)
Acc all            : 0.834 (260/1563)
Acc not rejected   : 0.998 (2/978)	rejected: 0.37 585/1563
Acc BA             : 1.000 (0/60)	rejected: 0.22 17/77
Acc GL             : 0.996 (1/249)	rejected: 0.14 39/288
Acc Customer       : 0.997 (1/381)	rejected: 0.39 245/626
Acc Vendor         : 1.000 (0/288)	rejected: 0.50 284/572
Docs ...
Acc all 0.909 (69/762) s:13, i:4, d:52	(rejected 454, no doc: 2325)

```

su `limit = 1.0`
```txt
Empty              : 0.537 (1563/3379)
Acc all            : 0.834 (260/1563)
Acc not rejected   : 0.993 (9/1291)	rejected: 0.17 272/1563
Acc BA             : 1.000 (0/76)	rejected: 0.01 1/77
Acc GL             : 0.976 (6/254)	rejected: 0.12 34/288
Acc Customer       : 0.997 (2/604)	rejected: 0.04 22/626
Acc Vendor         : 0.997 (1/357)	rejected: 0.38 215/572
Docs ...
Acc all 0.922 (83/1060) s:23, i:6, d:54	(rejected 156, no doc: 2325)
```

# Demo 4
2023 03 20

Rezultatai: H
```txt
Acc all        : 0.8862722573233773 (990/8705)
Acc not empty     : 0.9992228985882657 (6/7721)	rejected: 973
Acc not rec before: 1.0 (0/266)	rejected: 81
Acc rec before    : 0.999195171026157 (6/7455)	rejected: 892
Docs ...
Acc all 0.8097964376590331 (598/3144) s:138, i:38, d:422	(rejected 340, no doc: 6943)

Oracle acc 0.9491963260619977, (177/3484)
```

Rezultatai: U
```txt
Acc all        : 0.9894305612453912 (129/12205)
Acc not empty     : 0.9976042957455596 (29/12105)	rejected: 100
Acc rec before    : 0.9976042957455596 (29/12105)	rejected: 100
Docs ...
Acc all 0.7838273195876289 (1342/6208) s:438, i:143, d:761	(rejected 214, no doc: 9016)

Oracle acc 0.985518530052943, (93/6422)
```
# Demo 3

Rezultatai: H
```txt
[2023-01-24 13:41:19.509] INFO - Acc all        : 0.8586677208934572 (715/5059)
[2023-01-24 13:41:19.517] INFO - Acc not empty     : 0.9967875172097292 (14/4358)	rejected: 690
[2023-01-24 13:41:19.518] INFO - Acc not rec before: 1.0 (0/120)	rejected: 55
[2023-01-24 13:41:19.527] INFO - Acc rec before    : 0.9966965549787635 (14/4238)	rejected: 635
[2023-01-24 13:41:19.527] INFO - Docs ...
[2023-01-24 13:41:19.534] INFO - Acc all 0.6715456674473068 (561/1708) s:170, i:223, d:168	(rejected 285, no doc: 4008)

Oracle acc 0.7957852483692925, (407/1993)
```

Rezultatai: S
```txt
limit=1.5 skip=50
[2023-01-24 14:12:27.190] INFO - Acc all        : 0.9289222767986132 (246/3461)
[2023-01-24 14:12:27.194] INFO - Acc not empty     : 0.9990677439403356 (3/3218)	rejected: 182
[2023-01-24 14:12:27.195] INFO - Acc not rec before: 1.0 (0/347)	rejected: 31
[2023-01-24 14:12:27.199] INFO - Acc rec before    : 0.9989550679205852 (3/2871)	rejected: 151
[2023-01-24 14:12:27.199] INFO - Docs ...
[2023-01-24 14:12:27.210] INFO - Acc all 0.7932783766645529 (652/3154) s:314, i:137, d:201	(rejected 78, no doc: 1108)

Oracle acc 0.8791309669522643, (395/3268)

```


# Demo 2

## Duomenys

Tik unikalūs `Bank Statement Entry`.

Sumažėjo įrašų nuo `4213` iki `3511`

## Testavimo aplinka

"Playground" - bandom imituoti esamą situaciją, t.y. kokie SF įrašai yra aktyvūs esamu laiko momentu. Išmetam padengtus
įrašus pagal `Customer_Applications` ir `Vendor_Applications`

## Kriterijų svorių optimizavimas

```txt
has_past       0.9174
iban_match     0.8631
ext_doc        0.7779
name_sim       0.6607
payment_match  0.6208
name_eq        0.2819
curr_match     0.2430
amount_match   0.1783
due_date       0.0556
ext_doc_sim    0.0510
entry_date     0.0468
```

manual (cust/vend)= `137/3400`, docs: `765/3232` s:393, i:164, d:208

optim (cust/vend) = `115/3400`, docs: `756/3232` s:384, i:161, d:211

naudojant slenkstį = `0.999 (1/3182)`, rejected: `218`


### Su test/val imtimis

3000 įrašų optimizavimui, 511 - validavimui
```
### val set manual
Acc not empty     : 0.9448979591836735 (27/490)	rejected: 0

### val set OPTIM
Acc not empty     : 0.9510204081632653 (24/490)	rejected: 0

### su slenksčiu:
Acc not empty     : 1.0 (0/450)	rejected: 40
```

## SF numerio apytikslis palyginimas

Kriterijus ar SF nr yra *entry.msg* - 0, 1.

https://github.com/airenas/re-bankmap/blob/bd93bbe2898ebeb04e35bebea48a8d8977435b33/src/utils/similarity.py#L60

- Raidžių priekyje arba `0` praleidimas - `0.3`
- Simbolio sukeitimas - `0.4` ???
- Pask sk. praleidimas - `0.3` ???
- Žodis yra SF pabaiga, pvz.: `SB034451` ir `SF SB 034775,51` (1133)

## SF sugretinimo tyrimas

1. Nustatome GL, BA, VEND, CUST.
2. Jei [VEND, CUST], ieškome SF:

https://github.com/airenas/re-bankmap/blob/bd93bbe2898ebeb04e35bebea48a8d8977435b33/egs/cmp_matrix/local/predict_docs.py#L29

```
SF: 0.762 (776/3268)    (rejected 0)

Su atmetimo sleksčiu:
Acc all 0.797 (634/3125) s:304, i:134, d:196	(rejected 107, no doc: 1108)

Oracle SF acc: 
0.879, (395/3268) (nėra SF?, išmesta per anksti iš aktyvių, išankstinės?)
```
### Problemos

- Nepilnai apmokėta?
- Avansinis mokėjimas - bandys priskirti esančioms SF
Kada nuspręsti, kad negalima susieti
- Lieka kažkokia nepadengta suma?
- pranešime yra Sf numeris, bet nesisieja nei su vienu įrašu

### Pvz.:

OK: 3459, 51

Su grąžinimu: 727, 3457

Kita SF, negu mokėjimo paskirtyje: 3450 (SB033122 vs sb033032 ??)

Vend SF: 415 (kažkodėl 2), 496 (nebuvo duomenyse)

---

# Demo 1

## Duomenys

Bank Statement Entries

- 4213
- 3803 atpažinta prieš tai
- 410 neatpažinta, iš jų 61 nauji, nėra į ką atpažinti

Customer Entries Vendor Entries Bank Accounts GL Accounts

## Optimizavimo uždavinys

Kiekvienam `Bank Statement Entry` suskaičiuojame atstumą tarp kiekvieno `Customer Entries`, `Vendor Entries`
, `Bank Accounts`, `GL Accounts` įrašo. Parenkam geriausią Customer, Vendor, BA, GLA.

Kriterijai:

1) `cust.name == entr.desc` - [0,1]
2) vardo panašumas `cust.name vs entry.desc` - bag-of-words similarity + jaro_winkler [0-1]
3) `cust.iban == entry.iban` - [0,1]
4) entry.msg contains cust.ext_doc_no - [0,1]
5) ar buvo toks mokėjimas praeityje [0,1]
   yra `cust.no = entryprev.rec_no`,
   kur `entryprev.desc = entry.desc && entryprev.iban == entry.iban && entry.date > entryprev.date`

   sprendžia BankAccounts TextToAccountMapping

-

6) `cust.date - entry.date`
7) `cust.duedate - entry.date`
8) `cust.amount - entry.ammount`


9) `currency code` pajungti

## Results

Acc not empty    : 0.977 (94/4102)

su atpažinimo slenksčiu Acc w/o rejected : 0.990 (40/4048)


