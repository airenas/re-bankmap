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
	"SELECT company, count(*) as requests, max(entries) as entries, \
		sum(lines), sum(recommended), \
		TRUNC((100.0 * sum(recommended))/sum(lines)) as rec_percent, \
		max(trained) as trained_on, max(trained_date) as trained_date \
		FROM {} \
		WHERE $(filter) \
		GROUP BY company HAVING entries > 0 and trained >= 0 ORDER BY rec_percent desc, entries desc, date asc, requests desc, entries desc"

############################################
explore/by-company: ${out_dir}/log.parquet
	dsq ${out_dir}/log.parquet --pretty \
	"SELECT max(date), \
	    company, count(*) as requests, max(entries) as entries, \
		sum(lines), trunc(avg(lines)), sum(recommended), \
		TRUNC((100.0 * sum(recommended))/sum(lines)) as rec_percent, \
		max(trained) as trained, max(trained_date) as trained_date \
		FROM {} \
		WHERE $(filter) \
		GROUP BY company, date HAVING $(hfilter) ORDER BY date asc, rec_percent desc, requests desc, entries desc"

############################################
explore/company: ${out_dir}/log.parquet
	dsq ${out_dir}/log.parquet --pretty \
	"SELECT date, time, company, entries, lines, recommended, \
		TRUNC((100.0 * recommended)/lines) as rec_percent, \
		trained, trained_date \
		FROM {} \
		WHERE $(filter) \
		ORDER BY date asc, time asc, rec_percent desc, entries desc"
############################################
explore/by-company/short: ${out_dir}/log.parquet
	dsq ${out_dir}/log.parquet --pretty \
	"SELECT company, \
		sum(lines), sum(recommended), \
		TRUNC((100.0 * sum(recommended))/sum(lines)) as rec_percent, max(entries) as entries \
		FROM {} \
		WHERE $(filter) \
		GROUP BY company HAVING $(hfilter) ORDER BY rec_percent desc"

clean:
	# @echo -n "Drop $(out_dir)? Are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	rm -rf $(out_dir)
.PHONY: clean
.EXPORT_ALL_VARIABLES:
