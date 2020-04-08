import logging
import os
import tempfile
import time
from concurrent.futures.thread import ThreadPoolExecutor

import httpx
from httpx import HTTPError

from helm_client import HelmClient
from models import (
    LocustTest,
    Status
)

logger = logging.getLogger(__name__)


class LocustClusterManager:
    def __init__(self):
        self.__executor = ThreadPoolExecutor(max_workers=10)
        self.__helm_client = HelmClient()

    def __execute_command(self, command: str) -> int:
        return os.system(command)

    def __start(self, test: LocustTest):
        self.__stop(test)

        logger.info(f'Starting Locust cluster: {test.id}')
        test.status = Status.STARTING

        with tempfile.TemporaryDirectory() as dir:
            with open(f'{dir}/tasks.py', 'w+') as fh:
                fh.write(test.script)

            status = self.__execute_command(f'kubectl create configmap locust-tasks-{test.id} --from-file {dir}/') == 0

            if status:
                status = self.__helm_client.install('stable/locust', f'locust-{test.id}', {
                    'worker.config.configmapName': f'locust-tasks-{test.id}',
                    'master.config.target-host': test.host,
                    'worker.replicaCount': test.workers,
                    'worker.resources.limits.cpu': f'1000m',
                    'worker.resources.requests.cpu': '1000m',
                    'worker.resources.limits.memory': '1Gi',
                    'worker.resources.requests.memory': '1Gi'
                })

            if status:
                for i in range(1, 300):
                    # Check if other thread has stopped the test
                    if test.status == Status.STOPPING or test.status == Status.STOPPED:
                        logger.info(f'Locust cluster was stopped while starting: {test.id}')
                        return

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

    def __stop(self, test: LocustTest):
        logger.info(f'Stopping Locust cluster: {test.id}')
        test.status = Status.STOPPING

        self.__execute_command(f'kubectl delete configmap locust-tasks-{test.id}')
        status = self.__helm_client.uninstall(f'locust-{test.id}')

        if status:
            logger.info(f'Locust cluster stopped: {test.id}')
            test.status = Status.STOPPED
        else:
            logger.info(f'Failed to stop Locust cluster: {test.id}')

    def start(self, test: LocustTest):
        self.__executor.submit(self.__start, test)

    def stop(self, test: LocustTest):
        self.__executor.submit(self.__stop, test)
