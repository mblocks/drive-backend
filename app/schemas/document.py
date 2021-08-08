from typing import Optional, List
from pydantic import BaseModel
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
    id: int
    name: Optional[str] = None


class Document(DBBase):
    name: str
    type: str
    parent: Optional[str] = None


class DirCreate(BaseModel):
    name: str
    parent: Optional[str] = None
