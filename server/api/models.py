from uuid import UUID

from pydantic import BaseModel


class CreateLocustTestRequest(BaseModel):
    name: str
    host: str
    workers: int
    script: str


class UpdateLocustTestRequest(BaseModel):
    id: UUID
    name: str
    host: str
    workers: int
    script: str
