from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class Status(str, Enum):
    STOPPING = 'stopping'
    STOPPED = 'stopped'
    STARTING = 'starting'
    STARTED = 'started'
    RUNNING = 'running'


class LocustTest(BaseModel):
    id: UUID
    name: str
    host: str
    status: Status
    master_host: str
    workers: int
    script: str
