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
skip=0
top=20
limit=0.3
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
${out_dir}/entries.txt: ${out_dir}/entries.csv
	$(python_cmd) local/map_entries.py --input $^ \
	    --input_map ${out_dir}/extracted/$(extr_dir)/Bank_Account_Recognitions.csv > $@_
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
${out_dir}/l_entries.txt: ${out_dir}/cust_l_entries.txt ${out_dir}/vend_l_entries.txt ${out_dir}/gl_entries.txt \
        ${out_dir}/ba_entries.txt
	cat ${out_dir}/cust_l_entries.txt > $@
	tail -n +2 ${out_dir}/vend_l_entries.txt >> $@
	tail -n +2 ${out_dir}/gl_entries.txt >> $@
	tail -n +2 ${out_dir}/ba_entries.txt >> $@
${out_dir}/predicted.txt: ${out_dir}/entries.txt ${out_dir}/l_entries.txt # ${model}
	$(python_cmd) local/predict_simple.py --input ${out_dir}/entries.txt --ledgers ${out_dir}/l_entries.txt \
	    > $@_
	mv $@_ $@
${out_dir}/features.txt: ${out_dir}/entries.txt ${out_dir}/l_entries.txt
	$(python_cmd) local/make_features.py --input ${out_dir}/entries.txt --ledgers ${out_dir}/l_entries.txt > $@_
	mv $@_ $@
${out_dir}/cmp.txt compare: ${out_dir}/predicted.txt ${out_dir}/entries.txt
	$(python_cmd) local/compare.py --f1 ${out_dir}/entries.txt --f2  ${out_dir}/predicted.txt \
		--out ${out_dir}/cmp.txt  --skip ${skip} --limit ${limit}
>PHONY: compare
${model}: ${out_dir}/features.txt
	$(python_cmd) local/train_dt.py --input $^ --out $@
############################################
build: ${out_dir}/features.txt ${out_dir}/cmp.txt
.PHONY: build
train: ${model}
.PHONY: train
inspect: ${out_dir}/features.txt
	$(python_cmd) local/inspect_data.py --i $^
.PHONY: inspect
eval: ${out_dir}/cmp.txt
.PHONY: eval
sim: ${out_dir}/entries.txt ${out_dir}/l_entries.txt
	$(python_cmd) local/similarities.py --input ${out_dir}/entries.txt --ledgers ${out_dir}/l_entries.txt --i $(i) \
		--top ${top}
.PHONY: sim
############################################
clean:
	rm -rf $(out_dir)
clean/model:
	rm -rf $(model)
.PHONY: clean	
.EXPORT_ALL_VARIABLES:	
