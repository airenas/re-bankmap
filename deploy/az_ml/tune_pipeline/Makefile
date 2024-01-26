-include Makefile.options
-include ../../../.version
############################################
log=info
python_cmd=PYTHONPATH=../../../ LOG_LEVEL=$(log) python
VERSION?=$(version)
############################################
deploy: src/version.txt conda.yaml
	$(python_cmd) deploy.py --run deploy
test:
	$(python_cmd) deploy.py --run test
.PHONY: deploy	
src/version.txt:
	echo $(version) > src/version.txt
.PHONY: src/version.txt
conda.yaml: conda.yaml.in
	cat $< | envsubst > $@
############################################
clean/req:
	rm -f conda.yaml
############################################
.EXPORT_ALL_VARIABLES:
