.PHONY: init start-client start-server

init:
	@yarn --cwd client install
	@pip install -r server/requirements.txt

start-client:
	@yarn --cwd client start

start-server:
	@pushd server/; PYTHONPATH=. uvicorn --reload --reload-dir server main:app; popd