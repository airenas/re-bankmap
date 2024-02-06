-include Makefile.options
############################################
log=info
python_cmd=PYTHONPATH=../../../ LOG_LEVEL=$(log) python
############################################
deploy: src/version.txt conda.yaml
	$(python_cmd) deploy.py --run deploy
test:
	$(python_cmd) deploy.py --run test
remote/clean/runs:
	$(python_cmd) clean.py --run runs
remote/clean/experiments:
	$(python_cmd) clean.py --run experiments
.PHONY: deploy	
src/version.txt: Makefile.options
	echo $(VERSION) > src/version.txt
.PHONY: src/version.txt
conda.yaml: conda.yaml.in Makefile.options
	cat $< | envsubst > $@
############################################
clean/req:
	rm -f conda.yaml
############################################
.EXPORT_ALL_VARIABLES:
