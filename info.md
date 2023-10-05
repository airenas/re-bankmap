
2023 10 05

Darbai:
 - MS support
 - bandžiau Azure ML servisus

   apjungiami:
      - kodas
      - duomenys
      - compute clusters (automatic scaling)
      - rest endpoint
      - background jobs
 - nauja paieška      

Problemos:

## 1. Daug užklausų naktį vienu metu
- Padaryti asinchroninį bendravimą

```bash
     BF                    Azure servisai
     |                           | 
   1. užklausa      -> 
                    <- jobID
   
   2. ciklas kol `status != finished` 
     
     status(jobID)  ->
                    <- status

   3. 
      result(jobID) ->
                     <- result
   
```
Darbai:
   - Perkelti kodą iš funkcijos į Azure ML
   - Apkabinti Azure ML su Azure funkcijomis


### Alternatyvos 

- BF kažkaip išskaido laike užklausas

- BF pusėje kartoti nepavykusius kvietinius (retry with backoff)

- Pabandyti sudiegti kelias funkcijas skirtingais vardais ir per Gateway padalinti darbus



## 2. Timeout'ina slenksčių optimizavimo funkcija kai daugiau duomenų
### Padaryti optimizavimą and Azure ML

(Blob Storage event) -> Azure function -> Azure ML pipeline -> naujas cfg failas saugomas Blob Storage




## 3. Nauja paieška

Tikslas - padaryti rekomendavimo sistemų principu

Banko išrašas -> parametrai (data, msg, suma, iban, mokėtojas) -> embedding (ANN)-> vector x

SF eilutė -> parametrai (data, įmonė, sf, suma, įmonės iban) -> embedding (ANN) -> vector y

cos_sim(vector x, verctor y) = 1, arba -> 0, jei nepanašu









   
