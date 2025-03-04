############################################
-include Makefile.options
############################################
zip?=../../xx.zip
out_dir?=data
python_dir=${CURDIR}/../../src/utils
log?=INFO
python_cmd=PYTHONPATH=../../ LOG_LEVEL=$(log) python
############################################
${out_dir}/extracted: 
	mkdir -p $@
${out_dir}: 
	mkdir -p $@	
############################################
${out_dir}/extracted/.done: ${zip} | ${out_dir}/extracted
	unzip ${zip} -d ${out_dir}/extracted
	touch $@
${out_dir}/cmp.jsonl: ${out_dir}/extracted/.done
	$(python_cmd) local/prepare.py --input ${out_dir}/extracted/OldData.jsonl > $@_
	mv $@_ $@
calculate: ${out_dir}/cmp.jsonl
	$(python_cmd) local/errs.py --input ${out_dir}/cmp.jsonl  > ${out_dir}/err.jsonl
############################################
clean:
ifneq ($(force),1)	
	@echo -n "Drop $(out_dir)? Are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]
endif	
	rm -rf $(out_dir)
.PHONY: clean
.EXPORT_ALL_VARIABLES:
