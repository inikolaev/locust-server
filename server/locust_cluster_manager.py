import logging
import tempfile
import time
from concurrent.futures.thread import ThreadPoolExecutor

import httpx
from httpx import HTTPError

from helm_client import HelmClient
from kubernetes_client import KubernetesClient
from models import (
    LocustTest,
    Status
)

logger = logging.getLogger(__name__)


class LocustClusterManager:
    def __init__(self):
        self.__executor = ThreadPoolExecutor(max_workers=10)
        self.__helm_client = HelmClient()
        self.__kubernetes_client = KubernetesClient()

    def __create_configmap(self, test: LocustTest) -> bool:
        with tempfile.TemporaryDirectory() as dir:
            with open(f'{dir}/tasks.py', 'w+') as fh:
                fh.write(test.script)

            return self.__kubernetes_client.create(f'locust-tasks-{test.id}', 'configmap', ['--from-file', dir])

    def __delete_configmap(self, test: LocustTest) -> bool:
        return self.__kubernetes_client.delete(f'locust-tasks-{test.id}', 'configmap')

    def __start(self, test: LocustTest):
        self.__stop(test)

        logger.info(f'Starting Locust cluster: {test.id}')
        test.status = Status.STARTING

        if not self.__create_configmap(test):
            logger.info(f'Failed to create configmap: locust-tasks-{test.id}')
            return

        if not self.__helm_client.install('stable/locust', f'locust-{test.id}', {
            'worker.config.configmapName': f'locust-tasks-{test.id}',
            'master.config.target-host': test.host,
            'worker.replicaCount': test.workers,
            'worker.resources.limits.cpu': f'1000m',
            'worker.resources.requests.cpu': '1000m',
            'worker.resources.limits.memory': '1Gi',
            'worker.resources.requests.memory': '1Gi'
        }):
            logger.info(f'Failed to create Locust cluster: locust-{test.id}')
            self.__delete_configmap(test)
            return

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

    def __stop(self, test: LocustTest) -> bool:
        logger.info(f'Stopping Locust cluster: {test.id}')
        test.status = Status.STOPPING

        if not self.__delete_configmap(test):
            logger.info(f'Failed to delete config map: locust-tasks-{test.id}')
            return False

        if not self.__helm_client.uninstall(f'locust-{test.id}'):
            logger.info(f'Failed to stop Locust cluster: locust-{test.id}')
            return False

        logger.info(f'Locust cluster stopped: {test.id}')
        test.status = Status.STOPPED

        return True

    def start(self, test: LocustTest):
        self.__executor.submit(self.__start, test)

    def stop(self, test: LocustTest):
        self.__executor.submit(self.__stop, test)
