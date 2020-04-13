import uuid
from contextlib import AsyncExitStack
from typing import Dict

from fastapi import APIRouter
from httpx import AsyncClient
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import (
    Response,
    StreamingResponse,
    JSONResponse
)
from starlette.status import HTTP_404_NOT_FOUND

from models import LocustTest


def proxy(client: AsyncClient, tests: Dict[uuid.UUID, LocustTest]) -> APIRouter:
    app = APIRouter()

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

    @app.api_route("/{id}{path:path}", methods=['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT', 'TRACE'])
    async def proxy(id: uuid.UUID, path: str, request: Request):
        test = tests.get(id)

        if test:
            return await proxy_request(test.master_host, request)

        return JSONResponse({}, status_code=HTTP_404_NOT_FOUND)

    return app
