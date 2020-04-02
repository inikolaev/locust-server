import os
import tempfile
import uuid
from typing import (
    Dict,
    List
)

from fastapi import (
    FastAPI,
    Form
)
from pydantic import BaseModel
from starlette.responses import (
    FileResponse,
    RedirectResponse
)
from starlette.staticfiles import StaticFiles
from starlette.status import HTTP_302_FOUND


class LocustTest(BaseModel):
    id: uuid.UUID
    name: str
    host: str
    workers: int
    script: str


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
    async def post_tests(
        name: str = Form(...),
        host: str = Form(...),
        workers: int = Form(...),
        script: str = Form(...)
    ):
        global tests
        id = uuid.uuid4()
        tests[id] = LocustTest(id=id, name=name, host=host, workers=workers, script=script)

        return RedirectResponse('/', status_code=HTTP_302_FOUND)

    @app.get("/tests/{id}/start")
    def start_test(id: uuid.UUID):
        test = tests.get(id)

        if test:
            startLocust(test)

        return RedirectResponse('/', status_code=HTTP_302_FOUND)

    @app.get("/tests/{id}/stop")
    def stop_test(id: uuid.UUID):
        test = tests.get(id)

        if test:
            stopLocust(test)

        return RedirectResponse('/', status_code=HTTP_302_FOUND)

    return app


app = main()
