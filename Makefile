.PHONY: init start-client start-server

init:
	@yarn --cwd client install
	@pip install -r server/requirements.txt

start-client:
	@yarn --cwd client start

start-server:
	@PYTHONPATH=server uvicorn --reload --reload-dir server main:app