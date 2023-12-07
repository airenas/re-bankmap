
# Uždavinys

## pirminis

Banko eilutes priskirti vienam iš 4 tipų:
- kliento mokėjimas, 
- tiekėjo mokėjimas, 
- banko sąskaitos pervedimas, 
- ar didžiosios knygos mokėjimas

ir priskirti konkretų tiekėjo, kliento, BA, GL numerį 

Galimas: [0..n] banko išrašas <---> 1 kl./tiek/bd/gl numeris duomenų bazėje

## antrinis

jei klientas ir tiekėjas nustatytas, tada priskirti SF. SF gali ir nebūti DB - avansiniams mokėjimams.

Galimas ryšys [1..n] banko išrašas <---> [0..n] SF


# Dvi lentelės:
formatas csv
## eilutės iš banko
- entries.txt

### Laukai
|Laukas|Aprašymas|Pvz|
|-|-|-|
|Description|Mokėtojas|xxxxTA UAB|
|Message|Pranešimas|Uz paslaugas|
|CdtDbtInd|Crefit/debit|CRDT|
|Amount|Suma|1000|
|Date|Data||
|IBAN|mokėtojo IBAN|LT387xxxxxxxxxxxxxxxx6|
|E2EId|nenaudojamas kol kas||
|RecAccount|ką reikia atpažinti: tiekėjo, kliento, ba ar GL numeris DB|P000009|
|RecDoc|antrinis uždavinys, konkretūs SF numeriai|SB0000008|
|Recognized|nesvarbu||
|Currency||EUR|
|Docs|??? man reikia pasiaiškinti ar šis laukas, ar RecDoc||
|DocNo|nesvarbu||


RecAccount, RecDoc dabartinio įrašo atpažinimui nenaudojamas, bet jis gali būti naudojamas vėlesnių įrašų atpažinimui. 

Pvz.: įrašas (2023 12 01) -> panašus įrašas (2023 11 11) -> RecAcount -> Tiekėjas



## eilutės iš DB
- l_entries.txt 

4 tipai:
- Tiekėjo SF
- KLiento SF 
- Banko mokėjimų eilutės - BA
- DK eilutės -GL 

### Laukai
|Laukas|Aprašymas|Pvz|
|-|-|-|
|Type|Customer - kliento sf, Vendor - tiel sf, BA - banko mokėjimo įrašas, GL - dk įrašas|Customer|
|No|Kodas|P00174|
|Name|Įmonės pav, sąsk pav (BA, GL)|"BXXXXXRA, UAB"|
|IBAN|Įmonės IBAN, jei nurodyta DB||
|Document_No|vidinis dok Nr|PR000009|
|Document_Date|SF sukurimo data||
|Due_Date|Iki kada apmokėti SF||
|ExtDoc|SF numeris, patiekiamas klientui, tiekėjui, dažnai matomas mokėjimo msg|SB0300001|
|Amount|SF suma|213.59|
|Currency||EUR|
|Document_Type|SF, BA, GL - praktiškai atitinka Type|SF|


## Rezultatai dabar

Pirminio uždavinio šiems duomenims (paskutiniai 2000 įrašų)

```bash
Acc GL             : 1.000 (0/2)	rejected: 0.99 175/177
Acc BA             : 1.000 (0/9)	rejected: 0.87 62/71
Acc Vendor         : 1.000 (0/25)	rejected: 0.67 51/76
Acc Customer       : 0.994 (9/1410)	rejected: 0.03 42/1452

```
Sistema GL/BA/Tiekėjo šiai įmonei praktiškai neatpažinėja. Kiekvienai įmonei pagal istorinius duomenis nustatomi atpažinimo slenksčiai kiekvienam tipui. 

GL:  177 įrašai, 175 atsisakė atpažinti, 2 atpažino teisingai

Klientai: - 1452 įrašai, 42 atsisakė atpažinti, iš kitų 1410 padarė 9 klaidas


SF priskyrimo tikslumas:
```
Acc all 0.947 (99/1883) s:45, i:35, d:19	(rejected 63, no doc: 298)
```

## Info 

Dabar naudojami kriterijai atstumui skaičiuoti: https://github.com/airenas/re-bankmap/blob/b4d54d6d4e487f34e09c7b7de5ac9cf97fe4f12f/bankmap/similarity/similarities.py#L74C9-L74C9

Realizacijos schema: https://github.com/airenas/re-bankmap/blob/main/design/proto-v3.png
