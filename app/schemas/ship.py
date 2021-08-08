from typing import List, Optional
from pydantic import BaseModel
from .base import DBBase


class ShipBase(BaseModel):
    category: str
    parent: str
    object_id: str
    order:  Optional[int] = None
   

class ShipCreate(ShipBase):
    pass


class ShipUpdate(ShipBase):
    pass


class Ship(ShipBase, DBBase):
    pass

class ShipMove(BaseModel):
    target:  Optional[int] = None
    documents: List[int]

class ShipCopy(ShipMove):
    target:  Optional[int] = None
    documents: List[int]
