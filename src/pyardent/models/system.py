from datetime import datetime

import httpx
from pydantic import BaseModel, PrivateAttr

class SystemData(BaseModel):
    system_address: int
    system_name: str
    system_x: float
    system_y: float
    system_z: float
    system_sector: str
    updated_at: datetime

class System(SystemData):
    _client: httpx.Client = PrivateAttr()

    @classmethod
    def from_json(cls, client: httpx.Client, payload: dict) -> "System":
        instance = cls.model_validate(payload)
        instance._client = client
        return instance