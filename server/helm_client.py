import json
import logging
import subprocess
from typing import (
    Dict,
    List
)

logger = logging.getLogger(__name__)


class HelmClient:
    def __execute(self, args: List[str]) -> subprocess.CompletedProcess:
        command = ' '.join(args)
        logger.debug(f'Executing Helm command: {command}')

        return subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def __params(self, params: Dict[str, str]):
        return ','.join([
            f'{key}={value}'
            for key, value in params.items()
        ])

    def install(self, chart: str, name: str, params: Dict[str, str]):
        """
        stderr: Error: cannot re-use a name that is still in use
        """
        args = ['helm', 'install', '-o', 'json', name]

        if len(params):
            args += ['--set', self.__params(params)]

        args += [chart]

        process = self.__execute(args)

        if 'Error: cannot re-use a name that is still in use' in process.stderr:
            return True

        try:
            result = json.loads(process.stdout)
            description = result.get('info', {}).get('description', '')

            if description.lower() == 'install complete':
                return True
        except (TypeError, ValueError):
            logger.exception('Failed to parse Helm result')

        logger.debug(f'Helm failed to install release {name}')
        logger.debug(f'Helm install stdout: {process.stdout}')
        logger.debug(f'Helm install stderr: {process.stderr}')
        return False

    def uninstall(self, name: str):
        """
        stderr: Error: uninstall: Release not loaded: {name}: release: not found
        stdout: release "{name}" uninstalled
        """
        process = self.__execute(['helm', 'uninstall', name])

        if f'release "{name}" uninstalled' in process.stdout:
            return True

        if f'Error: uninstall: Release not loaded: {name}: release: not found' in process.stderr:
            return True

        logger.debug(f'Helm failed to uninstall release {name}')
        logger.debug(f'Helm uninstall stdout: {process.stdout}')
        logger.debug(f'Helm uninstall stderr: {process.stderr}')
        return False
