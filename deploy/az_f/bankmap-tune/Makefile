-include $(cfg)
-include ../../../.version
############################################
run/local:
	func start
update/bankmap:
	pip uninstall -y bankmap
############################################
# create/az-group:
# 	az group create --name $(func_resource_group) --location $(func_location)
# create/storage-account:
# 	az storage account create --name $(func_storage) --sku Standard_LRS --resource-group $(func_resource_group)
create/plan:
	az functionapp plan create --name bankmapPremiumPlan --resource-group $(func_resource_group) \
		--location $(func_location) --sku EP1 --is-linux true --max-burst 1
create/function:
	az functionapp create --consumption-plan-location $(func_location) --runtime python --runtime-version 3.8 \
		--functions-version 4 --name $(func_name) --os-type linux --storage-account $(func_storage) \
		--resource-group $(func_resource_group)
create/function/premium:
	az functionapp create --plan bankmapPremiumPlan --runtime python --runtime-version 3.8 \
		--functions-version 4 --name $(func_name) --os-type linux --storage-account $(func_storage) \
		--resource-group $(func_resource_group)		
############################################
delete/function:
	az functionapp delete --name $(func_name) --resource-group $(func_resource_group)
delete/plan:
	az functionapp plan delete --name bankmapPremiumPlan --resource-group $(func_resource_group)	

enable/indexing:		
	az functionapp config appsettings set --name $(func_name) --resource-group $(func_resource_group) --settings AzureWebJobsFeatureFlags=EnableWorkerIndexing		
get/storage-account/cs:
	func azure storage fetch-connection-string $(func_storage)
############################################
deploy: _version requirements.txt
	func azure functionapp publish $(func_name)
.PHONY: deploy	
requirements.txt: requirements.txt.in
	cat $< | envsubst > $@	
_version:
	echo $(version) > .version
############################################
# test/remote:
# 	curl -X POST https://$(func_name).azurewebsites.net/api/map?code=$(app_key) -i -H 'Accept: application/json' \
# 	    -H 'content-type: application/octet-stream' -H 'RecognitionForId: aHVt' --data-binary @test.zip
# test/remote/pretty:
# 	curl -X POST https://$(func_name).azurewebsites.net/api/map?code=$(app_key) -H 'Accept: application/json' \
# 	    -H 'content-type: application/octet-stream' -H 'RecognitionForId: aHVt' --data-binary @test.zip | jq .
# test/local:
# 	curl -X POST http://localhost:7071/api/map -i -H 'Accept: application/json' \
# 	    -H 'content-type: application/octet-stream' -H 'RecognitionForId: aHVt' --data-binary @test.zip
############################################
clean/req:
	rm -f requirements.txt
.PHONY: clean/req
############################################
.EXPORT_ALL_VARIABLES:

