-include Makefile.options
-include ../../../.version
############################################
run/local:
	func start
############################################
create/az-group:
	az group create --name $(func_resource_group) --location $(func_location)
create/storage-account:
	az storage account create --name $(func_storage) --sku Standard_LRS
create/function:
	az functionapp create --consumption-plan-location $(func_location) --runtime python --runtime-version 3.8 \
		--functions-version 4 --name $(func_name) --os-type linux --storage-account $(func_storage)
enable/indexing:		
	az functionapp config appsettings set --name $(func_name) --resource-group $(func_resource_group) --settings AzureWebJobsFeatureFlags=EnableWorkerIndexing		
get/storage-account/cs:
	func azure storage fetch-connection-string $(func_storage)
deploy: _version
	func azure functionapp publish $(func_name)
_version:
	echo $(version) > .version

test/remote:
	curl -X POST https://bankmap.azurewebsites.net/api/map?code=$(app_key) -i -H 'Accept: application/json' -H 'content-type: multipart/form-data' -F company=hum -F file=@test.zip
test/local:
	curl -X POST http://localhost:7071/api/map -i -H 'Accept: application/json' -H 'content-type: multipart/form-data' -F company=hum -F file=@test.zip
