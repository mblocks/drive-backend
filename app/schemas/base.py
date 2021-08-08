from typing import Optional
from pydantic import BaseModel


class DBBase(BaseModel):
    id: Optional[int] = None

    class Config:
        orm_mode = True
