
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

Pirminio uždavinio šiems duomenims (paskutiniai 2714 įrašų)

```bash
Acc BA             : 0.659 (14/41)	rejected: 0.59 59/100
Acc GL             : 0.995 (1/185)	rejected: 0.24 60/245
Acc Customer       : 0.999 (2/2041)	rejected: 0.09 205/2246
Acc Vendor         : 0.955 (2/44)	rejected: 0.61 68/112
```
Sistema BA/Tiekėjo šiai įmonei praktiškai neatpažinėja. Kiekvienai įmonei pagal istorinius duomenis nustatomi atpažinimo slenksčiai kiekvienam tipui. 

GL:  245 įrašai, 60 atsisakė atpažinti, 184 iš likusių 185 atpažino teisingai

Klientai: - 2246 įrašai, 205 atsisakė atpažinti, iš kitų 2041 padarė 2 klaidas


SF priskyrimo tikslumas:
```
Acc all 0.951 (128/2618) s:51, i:55, d:22	(rejected 358, no doc: 425)
```

## Info 

Dabar naudojami kriterijai atstumui skaičiuoti: https://github.com/airenas/re-bankmap/blob/6d497592378485d0f7b0c1c2350749cff6c36387/bankmap/similarity/similarities.py#L75

Realizacijos schema: https://github.com/airenas/re-bankmap/blob/main/design/proto-v3.png
