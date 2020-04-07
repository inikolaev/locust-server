import logging
import os
import tempfile
import time
from concurrent.futures.thread import ThreadPoolExecutor

import httpx
from httpx import HTTPError

from models import (
    LocustTest,
    Status
)

logger = logging.getLogger(__name__)


class LocustClusterManager:
    def __init__(self):
        self.__executor = ThreadPoolExecutor(max_workers=10)

    def __execute_command(self, command: str) -> int:
        return os.system(command)

    def __start(self, test: LocustTest):
        self.__stop(test)

        logger.info(f'Starting Locust cluster: {test.id}')

        with tempfile.TemporaryDirectory() as dir:
            with open(f'{dir}/tasks.py', 'w+') as fh:
                fh.write(test.script)

            status = self.__execute_command(f'kubectl create configmap locust-tasks-{test.id} --from-file {dir}/')

            if status == 0:
                status = self.__execute_command(
                    f'helm install locust-{test.id} --set worker.config.configmapName=locust-tasks-{test.id},master.config.target-host={test.host},worker.replicaCount={test.workers},worker.resources.limits.cpu=1000m,worker.resources.requests.cpu=1000m,worker.resources.limits.memory=1Gi,worker.resources.requests.memory=1Gi stable/locust')

            if status == 0:
                for i in range(1, 300):
                    # Check if other thread has stopped the test
                    if test.status == Status.STOPPING or test.status == Status.STOPPED:
                        break

                    logger.info(f'Waiting for Locust master to start: {test.master_host}')
                    try:
                        response = httpx.get(f'{test.master_host}/stats/requests')

                        if response.status_code == 200:
                            data = response.json()
                            if data['state'] == 'ready':
                                test.status = Status.STARTED
                                break
                    except HTTPError:
                        pass
                    except Exception:
                        logger.exception(f'Unexpected error during Locust cluster start: {test.id}')
                        self.__stop(test)
                        break

                    time.sleep(1)

                if test.status != Status.STARTED:
                    logger.info(f'Failed to start Locust cluster: {test.id}')
                    self.__stop(test)
            else:
                test.status = Status.STOPPED

    def __stop(self, test: LocustTest):
        logger.info(f'Stopping Locust cluster: {test.id}')
        self.__execute_command(f'kubectl delete configmap locust-tasks-{test.id}')
        status = self.__execute_command(f'helm uninstall locust-{test.id}')

        if status == 0:
            logger.info(f'Locust cluster stopped: {test.id}')
            test.status = Status.STOPPED
        else:
            logger.info(f'Failed to stop Locust cluster: {test.id}')
            test.status = Status.STARTED

    def start(self, test: LocustTest):
        self.__executor.submit(self.__start, test)

    def stop(self, test: LocustTest):
        self.__executor.submit(self.__stop, test)
