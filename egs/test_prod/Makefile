############################################
-include Makefile.options
############################################
data_dir?=../../data
out_dir?=data
python_dir=${CURDIR}/../../src/utils
log?=INFO
python_cmd=PYTHONPATH=../../ LOG_LEVEL=$(log) python
i?=0
top?=20
############################################
${out_dir}/extracted: 
	mkdir -p $@
${out_dir}: 
	mkdir -p $@	
############################################
${out_dir}/extracted/.done: ${zip} | ${out_dir}/extracted
	unzip ${zip} -d ${out_dir}/extracted
	touch $@
run: ${out_dir}/extracted/.done
	$(python_cmd) ../../bankmap/entry_mapper.py ${out_dir}/extracted
tune: ${out_dir}/extracted/.done
	$(python_cmd) ../../bankmap/tune_limits.py ${out_dir}/extracted
############################################
clean:
	# @echo -n "Drop $(out_dir)? Are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	rm -rf $(out_dir)
.PHONY: clean
.EXPORT_ALL_VARIABLES:
