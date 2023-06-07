############################################
-include Makefile.options
############################################
out_dir?=data
log?=INFO
python_cmd=PYTHONPATH=../../ LOG_LEVEL=$(log) python
############################################
${out_dir}:
	mkdir -p $@	
############################################
${out_dir}/log.parquet: $(logs) | ${out_dir}
	$(python_cmd) local/map_logs.py --input $(logs) --output $@
############################################
build: ${out_dir}/log.parquet
############################################
explore/by-date: 
	dsq ${out_dir}/log.parquet --pretty \
	"SELECT max(date), company, count(*) as requests, max(entries) as entries, \
		sum(lines), sum(recommended), \
		TRUNC((100.0 * sum(recommended))/sum(lines))/100.0 as rec_percent, \
		max(trained) as trained \
		FROM {} \
		WHERE $(filter) \
		GROUP BY company HAVING entries > 0 and trained >= 0 ORDER BY rec_percent desc, date asc, requests desc, entries desc"

############################################
explore/by-company: 
	dsq ${out_dir}/log.parquet --pretty \
	"SELECT max(date), company, count(*) as requests, max(entries) as entries, \
		sum(lines), trunc(avg(lines)), sum(recommended), \
		TRUNC((100.0 * sum(recommended))/sum(lines))/100.0 as rec_percent, \
		max(trained) as trained \
		FROM {} \
		GROUP BY company HAVING trained >= 0 ORDER BY rec_percent desc, date asc, requests desc, entries desc"

clean:
	# @echo -n "Drop $(out_dir)? Are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	rm -rf $(out_dir)
.PHONY: clean
.EXPORT_ALL_VARIABLES:
