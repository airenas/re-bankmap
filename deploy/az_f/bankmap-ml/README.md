## Installation


```bash
## azure functions cli
npm i -g azure-functions-core-tools@4 --unsafe-perm true
## python env
python -m venv .venv
source .venv/bin/activate
make requirements.txt
python -m pip install -r requirements.txt
make run/local
```