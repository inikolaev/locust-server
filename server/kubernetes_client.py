import logging
import subprocess
from typing import List

logger = logging.getLogger(__name__)


class KubernetesClient:
    def __execute(self, args: List[str]) -> subprocess.CompletedProcess:
        command = ' '.join(args)
        logger.debug(f'Executing kubectl command: {command}')

        return subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def create(self, name: str, type: str, args: List[str] = []) -> bool:
        args = ['kubectl', 'create', type, name] + args
        process = self.__execute(args)

        if f'{type}/{name} created' in process.stdout:
            return True

        if (
            f'Error from server (AlreadyExists): {type}s "{name}" already exists' in process.stderr
            or f'Error from server (AlreadyExists): {type} "{name}" already exists' in process.stderr
        ):
            return True

        logger.debug(f'kubectl failed to create {type} {name}')
        logger.debug(f'kubectl create stdout: {process.stdout}')
        logger.debug(f'kubectl create stderr: {process.stderr}')

        return False

    def delete(self, name: str, type: str, args: List[str] = []) -> bool:
        args = ['kubectl', 'delete', type, name] + args
        process = self.__execute(args)

        if f'{type} "{name}" deleted' in process.stdout:
            return True

        if (
            f'Error from server (NotFound): {type}s "{name}" not found' in process.stderr
            or f'Error from server (NotFound): {type} "{name}" not found' in process.stderr
        ):
            return True

        logger.debug(f'kubectl failed to delete {type} {name}')
        logger.debug(f'kubectl delete stdout: {process.stdout}')
        logger.debug(f'kubectl delete stderr: {process.stderr}')

        return False
