from typing import Optional
from pydantic import BaseModel, conint
from .base import DBBase


class DocumentBase(BaseModel):
    name: str
    type: str
    parent: Optional[str] = None
    path: Optional[str] = None


class DocumentCreate(BaseModel):
    name: str
    type: str
    parent: Optional[str] = None


class DocumentUpdate(BaseModel):
    id: conint(gt=0)
    name: Optional[str] = None


class Document(DBBase):
    name: str
    type: str
    parent: Optional[str] = None
    thumbnail: Optional[str] = None


class DirCreate(BaseModel):
    name: str
    parent: Optional[str] = None


class Dir(DBBase):
    name: str
    parent: Optional[str] = None
