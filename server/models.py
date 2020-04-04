from uuid import UUID

from pydantic import BaseModel


class LocustTest(BaseModel):
    id: UUID
    name: str
    host: str
    master_host: str
    workers: int
    script: str
