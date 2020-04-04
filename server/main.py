import os
import tempfile
import uuid
from contextlib import AsyncExitStack
from typing import (
    Dict,
    List
)

import httpx
from fastapi import FastAPI
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import (
    FileResponse,
    JSONResponse,
    StreamingResponse,
    Response
)
from starlette.staticfiles import StaticFiles
from starlette.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
)

from api.models import (
    CreateLocustTestRequest,
    UpdateLocustTestRequest
)
from models import LocustTest

tests: Dict[uuid.UUID, LocustTest] = {}


def execCommand(command: str) -> int:
    return os.system(command)


def startLocust(test: LocustTest):
    stopLocust(test)

    with tempfile.TemporaryDirectory() as dir:
        with open(f'{dir}/tasks.py', 'w+') as fh:
            fh.write(test.script)

        execCommand(f'kubectl create configmap locust-tasks-{test.id} --from-file {dir}/')
        execCommand(f'helm install locust-{test.id} --set worker.config.configmapName=locust-tasks-{test.id},master.config.target-host={test.host},worker.replicaCount={test.workers},worker.resources.limits.cpu=1000m,worker.resources.requests.cpu=1000m,worker.resources.limits.memory=1Gi,worker.resources.requests.memory=1Gi stable/locust')


def stopLocust(test: LocustTest):
    execCommand(f'kubectl delete configmap locust-tasks-{test.id}')
    execCommand(f'helm uninstall locust-{test.id}')


def main() -> FastAPI:
    client = httpx.AsyncClient()

    app = FastAPI()
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/")
    def root():
        return FileResponse('./index.html')

    @app.get("/tests")
    async def get_tests() -> List[LocustTest]:
        return list(tests.values())

    @app.post("/tests")
    async def post_tests(request: CreateLocustTestRequest):
        global tests
        id = uuid.uuid4()
        tests[id] = LocustTest(id=id, master_host=f'http://locust-{id}:8089', **request.dict())

    @app.put("/tests/{id}")
    async def put_tests(id: uuid.UUID, request: UpdateLocustTestRequest):
        global tests

        if id in tests:
            tests[id] = LocustTest(**request.dict())
            return JSONResponse({}, status_code=HTTP_200_OK)

        return JSONResponse({}, status_code=HTTP_404_NOT_FOUND)

    @app.delete("/tests/{id}")
    async def delete_tests(id: uuid.UUID):
        global tests

        if id in tests:
            del tests[id]
            return JSONResponse({}, status_code=HTTP_200_OK)

        return JSONResponse({}, status_code=HTTP_404_NOT_FOUND)

    @app.post("/tests/{id}/start")
    def start_test(id: uuid.UUID):
        test = tests.get(id)

        if test:
            startLocust(test)
            return JSONResponse({}, status_code=HTTP_200_OK)

        return JSONResponse({}, status_code=HTTP_404_NOT_FOUND)

    @app.post("/tests/{id}/stop")
    def stop_test(id: uuid.UUID):
        test = tests.get(id)

        if test:
            stopLocust(test)
            return JSONResponse({}, status_code=HTTP_200_OK)

        return JSONResponse({}, status_code=HTTP_404_NOT_FOUND)

    async def proxy_request(base_url: str, request: Request) -> Response:
        path = '/'.join(request.url.path.split('/')[3:])
        url = f'{base_url}/{path}?{request.url.query}'

        exit_stack = AsyncExitStack()
        response = await exit_stack.enter_async_context(
            client.stream(
                method=request.method,
                url=url,
                data=request.stream(),
                headers=request.headers.items())
        )
        return StreamingResponse(
            response.aiter_raw(),
            status_code=response.status_code,
            headers=response.headers,
            background=BackgroundTask(exit_stack.aclose),
        )

    @app.get("/proxy/{id}/?")
    async def proxy(id: uuid.UUID, request: Request):
        test = tests.get(id)

        if test:
            return await proxy_request(test.master_host, request)

        return JSONResponse({}, status_code=HTTP_404_NOT_FOUND)

    @app.get("/proxy/{id}/{path:path}")
    async def proxy_get(id: uuid.UUID, path: str, request: Request):
        test = tests.get(id)

        if test:
            return await proxy_request(test.master_host, request)

        return JSONResponse({}, status_code=HTTP_404_NOT_FOUND)

    @app.post("/proxy/{id}/{path:path}")
    async def proxy_post(id: uuid.UUID, path: str, request: Request):
        test = tests.get(id)

        if test:
            return await proxy_request(test.master_host, request)

        return JSONResponse({}, status_code=HTTP_404_NOT_FOUND)

    return app


app = main()
