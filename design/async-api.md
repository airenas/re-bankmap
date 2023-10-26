
## Info
Request timeout'as visiems kvietiniams = 1m. 

Kiek aš bandžiau funkcija į užklausą atsako per 3-10s, bet jei `cold` startas, kvietinys užtrunka 30-60s. `Cold`` startas vyksta, jei funkcija nebuvo kviesta per paskutines 5m.

## 1. Siunčiame atpažinimui, gauname `job_id`
Kvietinys toks pat kaip ir dabartinis
```bash
curl -X POST https://bankmap-ml.azurewebsites.net/api/map?code=<api_code> -i -H 'Accept: application/json' \
    -H 'content-type: application/octet-stream' -H 'RecognitionForId: aHVt' --data-binary @../bankmap/test.zip
```
`RecognitionForId` - base64 koduotas įmonės pavadinimas. Siunčiamas `body` - zip failas

### Atsakymas
```txt
HTTP/2 200
content-type: application/json
date: Thu, 26 Oct 2023 10:09:28 GMT
```
```json
{"company": "hum", "id": "01HDNPX9GEH70Y5QS65E3WSYSA", "job_id": "lucid_school_dqmm25308q", "metrics": {"extract_zip_sec": 1.4615168571472168, "copy_to_storage_sec": 0.07217025756835938, "map_sec": 25.5330867767334, "total_sec": 27.06677746772766}, "info": {"app_version": "0.2.290-beta"}}
```
Jei 2xx - įsimename `"job_id": "lucid_school_dqmm25308q"`

Jei 404, 429, 5xx - `retry su backoff`

Jei nepavyksta 3 kartus - loginam klaidą 

## 2. Tikriname užduoties statusą siųsdami `job_id`
 ```bash
curl -X GET https://bankmap-ml.azurewebsites.net/api/status/<job_id>?code=<api_code> -i -H 'Accept: application/json'
```
### Atsakymas
```txt
HTTP/2 200
content-type: application/json
date: Thu, 26 Oct 2023 10:16:39 GMT
```
```json
{"status": "Completed", "job_id": "lucid_school_dqmm25308q"}
```
galimi `status`: https://learn.microsoft.com/en-us/python/api/azure-ai-ml/azure.ai.ml.entities.job?view=azure-python#azure-ai-ml-entities-job-status

Tikrinimo algoritmas siūlomas toks:
```bash
wait_till = 30m + now()
while now() < wait_till {
    sleep (1m * rand[0,1])
    status = get_status(job_id, request_timeout=1m)
    if status == 'Completed' {
        return ok
    }
    if status in ['Failed', 'Canceled'] {
        log(error=failed)
        return failed
    }
}
log (error=timeout)
return failed
```


## 3. Paimame rezultatą pagal `job_id`, kai `status == Completed`

```bash
curl -X GET https://bankmap-ml.azurewebsites.net/api/result/<job_id>?code=<api_code> -H 'Accept: application/json' -i 
```
### Atsakymas
JSON tas pats, nepasikeitęs, kaip ir dabartinėje funkcijoje
```txt
HTTP/2 200
content-type: application/json
date: Thu, 26 Oct 2023 10:49:20 GMT
```
```json
{"company": "hum", "mappings": [{"entry": ....
```

Jei 2xx - apdorojame rezultatą

Jei 404, 429, 5xx - `retry su backoff`

Jei nepavyksta 3 kartus - loginam klaidą 
