.PHONY: init
init:
	@yarn --cwd client install
	@pip install -r server/requirements.txt

.PHONY: start-client
start-client:
	@yarn --cwd client start

.PHONY: start-server
start-server:
	@pushd server/; PYTHONPATH=. uvicorn --reload --reload-dir . --log-config logging.conf main:app; popd

.PHONY: build
build:
	@docker build -t inikolaev/locust-server .