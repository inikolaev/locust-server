.PHONY: init start-client start-server build

init:
	@yarn --cwd client install
	@pip install -r server/requirements.txt

start-client:
	@yarn --cwd client start

start-server:
	@pushd server/; PYTHONPATH=. uvicorn --reload --reload-dir . --log-config logging.conf main:app; popd

build:
	@docker build -t inikolaev/locust-server .