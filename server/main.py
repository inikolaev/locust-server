import logging
import os
import tempfile
import time
import uuid
from contextlib import AsyncExitStack
from threading import Thread
from typing import (
    Dict,
    List
)

import httpx
from fastapi import FastAPI
from httpx import (
    NetworkError,
    HTTPError
)
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
from locust_cluster_manager import LocustClusterManager
from models import (
    LocustTest,
    Status
)

logger = logging.getLogger(__name__)

tests: Dict[uuid.UUID, LocustTest] = {}


def main() -> FastAPI:
    client = httpx.AsyncClient()

    locust_cluster_manager = LocustClusterManager()

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
        tests[id] = LocustTest(
            id=id,
            master_host=f'http://locust-{id}-master-svc:8089',
            status=Status.STOPPED,
            **request.dict()
        )

    @app.put("/tests/{id}")
    async def put_tests(id: uuid.UUID, request: UpdateLocustTestRequest):
        global tests

        if id in tests:
            tests[id] = tests[id].copy(update=request.dict(exclude={'id'}))
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
            test.status = Status.STARTING
            locust_cluster_manager.start(test)
            return JSONResponse({}, status_code=HTTP_200_OK)

        return JSONResponse({}, status_code=HTTP_404_NOT_FOUND)

    @app.post("/tests/{id}/stop")
    def stop_test(id: uuid.UUID):
        test = tests.get(id)

        if test:
            test.status = Status.STOPPING
            locust_cluster_manager.stop(test)
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

