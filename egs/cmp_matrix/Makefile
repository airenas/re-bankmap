############################################
-include Makefile.options
############################################
data_dir?=../../data
zip?=Softera_data_v1.zip
out_dir?=data
extr_dir?=Softera_data_v1
python_dir=${CURDIR}/../../src/utils
python_cmd=PYTHONPATH=../../ LOG_LEVEL=INFO python
i?=0
take_n?=100000000000000
model?=${out_dir}/dt.model
batch?=10
hidden?=10
skip?=0
split?=3000
top?=20
limit?=1.5
############################################
${out_dir}/extracted: 
	mkdir -p $@
${out_dir}: 
	mkdir -p $@	
############################################
${out_dir}/extracted/.done: $(data_dir)/${zip} | ${out_dir}/extracted
	unzip $(data_dir)/${zip} -d ${out_dir}/extracted
	touch $@
${out_dir}/entries.csv: ${out_dir}/extracted/.done
	cat ${out_dir}/extracted/$(extr_dir)/Bank_Statement_Entries.csv | head -n $(take_n) > $@
${out_dir}/docs_map.txt: ${out_dir}/c_docs_map.txt ${out_dir}/v_docs_map.txt
	cat ${out_dir}/c_docs_map.txt > $@
	tail -n +2 ${out_dir}/v_docs_map.txt >> $@
${out_dir}/c_docs_map.txt: ${out_dir}/extracted/.done
	$(python_cmd) local/extract_docs.py --name Cust \
	    --input ${out_dir}/extracted/$(extr_dir)/Customer_Applications.csv > $@_
	mv $@_ $@
${out_dir}/v_docs_map.txt: ${out_dir}/extracted/.done
	$(python_cmd) local/extract_docs.py --name Vend \
	    --input ${out_dir}/extracted/$(extr_dir)/Vendor_Applications.csv > $@_
	mv $@_ $@		
${out_dir}/entries.txt: ${out_dir}/entries.csv ${out_dir}/docs_map.txt
	$(python_cmd) local/map_entries.py --input ${out_dir}/entries.csv \
	    --input_map ${out_dir}/extracted/$(extr_dir)/Bank_Account_Recognitions.csv \
	    --docs_map ${out_dir}/docs_map.txt > $@_
	mv $@_ $@
${out_dir}/cust_l_entries.txt: ${out_dir}/extracted/.done
	$(python_cmd) local/map_customers.py --input ${out_dir}/extracted/$(extr_dir)/Customer > $@_
	mv $@_ $@
${out_dir}/gl_entries.txt: ${out_dir}/extracted/.done
	$(python_cmd) local/map_gl.py --input ${out_dir}/extracted/$(extr_dir)/GL_Accounts.csv > $@_
	mv $@_ $@
${out_dir}/ba_entries.txt: ${out_dir}/extracted/.done
	$(python_cmd) local/map_ba.py --input ${out_dir}/extracted/$(extr_dir)/Bank_Accounts.csv > $@_
	mv $@_ $@
${out_dir}/vend_l_entries.txt: ${out_dir}/extracted/.done
	$(python_cmd) local/map_vendors.py --input ${out_dir}/extracted/$(extr_dir)/Vendor > $@_
	mv $@_ $@
${out_dir}/cust_l_apps.txt: ${out_dir}/extracted/.done
	$(python_cmd) local/map_customers_app.py --input ${out_dir}/extracted/$(extr_dir)/Customer_Applications.csv > $@_
	mv $@_ $@
${out_dir}/vend_l_apps.txt: ${out_dir}/extracted/.done
	$(python_cmd) local/map_vendors_app.py --input ${out_dir}/extracted/$(extr_dir)/Vendor_Applications.csv > $@_
	mv $@_ $@			
${out_dir}/l_entries.txt: ${out_dir}/cust_l_entries.txt ${out_dir}/vend_l_entries.txt ${out_dir}/gl_entries.txt \
        ${out_dir}/ba_entries.txt
	cat ${out_dir}/cust_l_entries.txt > $@
	tail -n +2 ${out_dir}/vend_l_entries.txt >> $@
	tail -n +2 ${out_dir}/gl_entries.txt >> $@
	tail -n +2 ${out_dir}/ba_entries.txt >> $@
${out_dir}/l_apps.txt: ${out_dir}/cust_l_apps.txt ${out_dir}/vend_l_apps.txt 
	cat ${out_dir}/cust_l_apps.txt > $@
	tail -n +2 ${out_dir}/vend_l_apps.txt >> $@
${out_dir}/predicted.txt: ${out_dir}/entries.txt ${out_dir}/l_entries.txt ${out_dir}/l_apps.txt # ${model}
	$(python_cmd) local/predict_play.py --input ${out_dir}/entries.txt --ledgers ${out_dir}/l_entries.txt \
	    --apps ${out_dir}/l_apps.txt > $@_
# 	$(python_cmd) local/predict_simple.py --input ${out_dir}/entries.txt --ledgers ${out_dir}/l_entries.txt \
# 	    > $@_
	mv $@_ $@
${out_dir}/features.txt: ${out_dir}/entries.txt ${out_dir}/l_entries.txt
	$(python_cmd) local/make_features.py --input ${out_dir}/entries.txt --ledgers ${out_dir}/l_entries.txt > $@_
	mv $@_ $@
${out_dir}/cmp.txt compare: ${out_dir}/predicted.txt ${out_dir}/entries.txt
	$(python_cmd) local/compare.py --f1 ${out_dir}/entries.txt --f2  ${out_dir}/predicted.txt \
		--out ${out_dir}/cmp.txt  --skip ${skip} --limit ${limit}
.PHONY: compare
${model}: ${out_dir}/features.txt
	$(python_cmd) local/train_dt.py --input $^ --out $@
show/oracle: ${out_dir}/entries.txt ${out_dir}/l_entries.txt ${out_dir}/l_apps.txt # ${model}
	$(python_cmd) local/oracle_docs.py --input ${out_dir}/entries.txt --ledgers ${out_dir}/l_entries.txt \
	    --apps ${out_dir}/l_apps.txt
show/sf: ${out_dir}/entries.txt ${out_dir}/l_entries.txt
	$(python_cmd) local/show_sf.py --input ${out_dir}/entries.txt --ledgers ${out_dir}/l_entries.txt
show/params:
	$(python_cmd) local/show_params.py
############################################
build: ${out_dir}/features.txt ${out_dir}/cmp.txt
.PHONY: build
train: ${model}
.PHONY: train
inspect: ${out_dir}/features.txt
	$(python_cmd) local/inspect_data.py --i $^
inspect/entries: ${out_dir}/entries.txt
	$(python_cmd) local/inspect_entries.py --i $^	
.PHONY: inspect
eval: ${out_dir}/cmp.txt
.PHONY: eval
sim: ${out_dir}/entries.txt ${out_dir}/l_entries.txt ${out_dir}/l_apps.txt
	$(python_cmd) local/sim_play.py --input ${out_dir}/entries.txt --ledgers ${out_dir}/l_entries.txt --i $(i) \
		--top ${top} --apps ${out_dir}/l_apps.txt
.PHONY: sim
############################################
inspect/play: ${out_dir}/l_entries.txt ${out_dir}/l_apps.txt
	$(python_cmd) local/inspect_play.py --ledgers ${out_dir}/l_entries.txt --c $(ic) \
		--doc ${idoc} --apps ${out_dir}/l_apps.txt --date "$(idate)"
.PHONY: inspect/play
############################################
${out_dir}/params.txt: ${out_dir}/entries.txt ${out_dir}/l_entries.txt ${out_dir}/l_apps.txt
	$(python_cmd) local/tune_params.py --input ${out_dir}/entries.txt --ledgers ${out_dir}/l_entries.txt \
	    --apps ${out_dir}/l_apps.txt --skip $(skip) --split_at $(split) --out $@_
	mv $@_ $@
tune: ${out_dir}/params.txt
############################################
clean:
	@echo -n "Drop $(out_dir)? Are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	rm -rf $(out_dir)
clean/model:
	rm -rf $(model)
.PHONY: clean	
.EXPORT_ALL_VARIABLES:	
