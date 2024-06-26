############################################
cfg?=cfg/hum_v2
-include $(cfg)
############################################
data_dir?=../../data
zip?=
out_dir?=data
extr_dir?=
log?=INFO
python_cmd=PYTHONPATH=../../ LOG_LEVEL=$(log) python
i?=0
take_n?=100000000000000
model?=${out_dir}/model
batch?=10
hidden?=10
skip?=0
split?=3000
top?=20
limit?=1.5
# year
hist=356
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
	$(python_cmd) ../cmp_matrix/local/extract_docs.py --name Cust \
	    --input ${out_dir}/extracted/$(extr_dir)/Customer_Recognitions.csv > $@_
	mv $@_ $@
${out_dir}/v_docs_map.txt: ${out_dir}/extracted/.done
	$(python_cmd) ../cmp_matrix/local/extract_docs.py --name Vend \
	    --input ${out_dir}/extracted/$(extr_dir)/Vendor_Recognitions.csv > $@_
	mv $@_ $@		
${out_dir}/entries.txt: ${out_dir}/entries.csv ${out_dir}/docs_map.txt
	$(python_cmd) ../cmp_matrix/local/map_entries.py --input ${out_dir}/entries.csv \
	    --input_map ${out_dir}/extracted/$(extr_dir)/Bank_Account_Recognitions.csv \
	    --docs_map ${out_dir}/docs_map.txt > $@_
	mv $@_ $@
${out_dir}/entries_test.txt ${out_dir}/entries_train.txt: ${out_dir}/entries.txt
	$(python_cmd) ../cmp_matrix/local/split.py --input ${out_dir}/entries.txt \
	    --split $(split) --out_test ${out_dir}/entries_test.txt --out_train ${out_dir}/entries_train.txt	
${out_dir}/cust_l_entries.txt: ${out_dir}/extracted/.done
	$(python_cmd) ../cmp_matrix/local/map_customers.py --input ${out_dir}/extracted/$(extr_dir)/Customer > $@_
	mv $@_ $@
${out_dir}/gl_entries.txt: ${out_dir}/extracted/.done
	$(python_cmd) ../cmp_matrix/local/map_gl.py --input ${out_dir}/extracted/$(extr_dir)/GL_Accounts.csv > $@_
	mv $@_ $@
${out_dir}/ba_entries.txt: ${out_dir}/extracted/.done
	$(python_cmd) ../cmp_matrix/local/map_ba.py --input ${out_dir}/extracted/$(extr_dir)/Bank_Accounts.csv > $@_
	mv $@_ $@
${out_dir}/vend_l_entries.txt: ${out_dir}/extracted/.done
	$(python_cmd) ../cmp_matrix/local/map_vendors.py --input ${out_dir}/extracted/$(extr_dir)/Vendor > $@_
	mv $@_ $@
##### map apps ################################
${out_dir}/cust_l_apps.txt: ${out_dir}/extracted/.done ${out_dir}/l_entries.txt
	$(python_cmd) ../cmp_matrix/local/map_customers_app.py --input ${out_dir}/extracted/$(extr_dir)/Customer_Applications.csv \
		--ledgers ${out_dir}/l_entries.txt > $@_
	mv $@_ $@
${out_dir}/vend_l_apps.txt: ${out_dir}/l_entries.txt ${out_dir}/extracted/.done
	$(python_cmd) ../cmp_matrix/local/map_vendors_app.py --input ${out_dir}/extracted/$(extr_dir)/Vendor_Applications.csv \
		--ledgers ${out_dir}/l_entries.txt > $@_
	mv $@_ $@
##### ledger entries ##########################				
${out_dir}/l_entries.txt: ${out_dir}/cust_l_entries.txt ${out_dir}/vend_l_entries.txt ${out_dir}/gl_entries.txt \
        ${out_dir}/ba_entries.txt
	cat ${out_dir}/cust_l_entries.txt > $@
	tail -n +2 ${out_dir}/vend_l_entries.txt >> $@
	tail -n +2 ${out_dir}/gl_entries.txt >> $@
	tail -n +2 ${out_dir}/ba_entries.txt >> $@
${out_dir}/l_apps.txt: ${out_dir}/cust_l_apps.txt ${out_dir}/vend_l_apps.txt 
	cat ${out_dir}/cust_l_apps.txt > $@
	tail -n +2 ${out_dir}/vend_l_apps.txt >> $@
${out_dir}/features.train.bin: ${out_dir}/entries_train.txt ${out_dir}/l_entries.txt ${out_dir}/l_apps.txt
	$(python_cmd) local/make_features.py --input ${out_dir}/entries_train.txt --ledgers ${out_dir}/l_entries.txt \
	    --apps ${out_dir}/l_apps.txt --history $(hist) --out $@_
	mv $@_ $@
${out_dir}/features.test.bin: ${out_dir}/entries_test.txt ${out_dir}/l_entries.txt ${out_dir}/l_apps.txt
	$(python_cmd) local/make_features.py --input ${out_dir}/entries_test.txt --ledgers ${out_dir}/l_entries.txt \
	    --apps ${out_dir}/l_apps.txt --history $(hist) --out $@_
	mv $@_ $@	
${out_dir}/model: ${out_dir}/features.train.bin 
	$(python_cmd) local/train_play.py --input ${out_dir}/features.train.bin --out $@_
	mv $@_ $@
${out_dir}/predicted_type.txt: ${out_dir}/model ${out_dir}/features.test.bin
	$(python_cmd) local/predict.py --input ${out_dir}/features.test.bin  --model ${out_dir}/model --out $@_
	mv $@_ $@
${out_dir}/predicted.txt: ${out_dir}/entries_test.txt ${out_dir}/l_entries.txt ${out_dir}/l_apps.txt ${out_dir}/predicted_type.txt
	$(python_cmd) ../cmp_matrix/local/predict_play_docs.py --input ${out_dir}/entries_test.txt --ledgers ${out_dir}/l_entries.txt \
	    --apps ${out_dir}/l_apps.txt --pred ${out_dir}/predicted_type.txt > $@_
	mv $@_ $@
${out_dir}/cmp.txt compare: ${out_dir}/predicted.txt ${out_dir}/entries_test.txt
	$(python_cmd) local/compare.py --f1 ${out_dir}/entries_test.txt --f2  ${out_dir}/predicted.txt \
		--out ${out_dir}/cmp.txt  --skip ${skip} --limit ${limit}
.PHONY: compare
show/errs-docs: ${out_dir}/cmp.txt.docs
	cat $^ | grep diff | grep -v rejected
show/errs: ${out_dir}/cmp.txt
	cat $^ | grep diff | grep -v rejected
############################################
build: ${out_dir}/features.txt ${out_dir}/cmp.txt
.PHONY: build
train: ${model}
.PHONY: train
eval: ${out_dir}/cmp.txt
.PHONY: eval
sim: ${out_dir}/entries_test.txt ${out_dir}/l_entries.txt ${out_dir}/l_apps.txt ${out_dir}/model
	$(python_cmd) local/sim_play.py --input ${out_dir}/entries_test.txt --ledgers ${out_dir}/l_entries.txt --i $(i) \
		--top ${top} --apps ${out_dir}/l_apps.txt --history $(hist) --model ${out_dir}/model
.PHONY: sim
############################################
inspect/play: ${out_dir}/l_entries.txt ${out_dir}/l_apps.txt
	$(python_cmd) local/inspect_play.py --ledgers ${out_dir}/l_entries.txt --c $(ic) \
		--doc ${idoc} --apps ${out_dir}/l_apps.txt --date "$(idate)"
.PHONY: inspect/play
############################################
clean:
ifneq ($(force),1)	
	@echo -n "Drop $(out_dir)? Are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]
endif	
	rm -rf $(out_dir)
.PHONY: clean
clean/model:
	rm -fr ${out_dir}/model
.EXPORT_ALL_VARIABLES:
