############################################
-include Makefile.options
############################################
out_dir?=data
log?=INFO
python_cmd=PYTHONPATH=../../ LOG_LEVEL=$(log) python
filter?=1=1
hfilter?=1=1
############################################
${out_dir}:
	mkdir -p $@	
############################################
${out_dir}/log.parquet: $(logs) | ${out_dir}
	$(python_cmd) local/map_logs.py --input $(logs) --output $@
############################################
build: ${out_dir}/log.parquet
############################################
explore/by-date: ${out_dir}/log.parquet
	dsq ${out_dir}/log.parquet --pretty \
	"SELECT * \
	    FROM {} \
		WHERE $(filter) AND date >= '20230804' \
		ORDER BY date desc, time desc"

############################################
clean:
	# @echo -n "Drop $(out_dir)? Are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	rm -rf $(out_dir)
.PHONY: clean
.EXPORT_ALL_VARIABLES:
