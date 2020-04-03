import os
import tempfile
import uuid
from typing import (
    Dict,
    List
)

from fastapi import FastAPI
from starlette.responses import (
    FileResponse,
    JSONResponse
)
from starlette.staticfiles import StaticFiles
from starlette.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
)

from server.api.models import (
    CreateLocustTestRequest,
    UpdateLocustTestRequest
)
from server.models import LocustTest

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
        tests[id] = LocustTest(id=id, **request.dict())

    @app.put("/tests/{id}")
    async def put_tests(id: uuid.UUID, request: UpdateLocustTestRequest):
        global tests

        if id in tests:
            tests[id] = LocustTest(**request.dict())
            return JSONResponse({}, status_code=HTTP_200_OK)
        else:
            return JSONResponse({}, status_code=HTTP_404_NOT_FOUND)

    @app.delete("/tests/{id}")
    async def delete_tests(id: uuid.UUID):
        global tests

        if id in tests:
            del tests[id]
            return JSONResponse({}, status_code=HTTP_200_OK)
        else:
            return JSONResponse({}, status_code=HTTP_404_NOT_FOUND)

    @app.post("/tests/{id}/start")
    def start_test(id: uuid.UUID):
        test = tests.get(id)

        if test:
            startLocust(test)

        return JSONResponse({}, status_code=HTTP_200_OK)

    @app.post("/tests/{id}/stop")
    def stop_test(id: uuid.UUID):
        test = tests.get(id)

        if test:
            stopLocust(test)

        return JSONResponse({}, status_code=HTTP_200_OK)

    return app


app = main()
