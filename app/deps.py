# -*- coding: utf-8 -*-
from fastapi import Request
from minio import Minio
from app.db.session import SessionLocal
from app.schemas import CurrentUser
from app.config import get_settings

settings = get_settings()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request):
    return CurrentUser(id=request.headers.get('x-consumer-id', 1),
                       third=request.headers.get(
                           'x-consumer-third', 'mblocks'),
                       third_user_id=request.headers.get(
                           'x-consumer-third-user-id', '1'),
                       third_user_name=request.headers.get(
                           'x-consumer-third-user-name', 'lizhixin')
                       # third_user_name=request.headers.get('x-consumer-third-user-name','').encode("Latin-1").decode("utf-8"),
                       )


def get_minio():
    return Minio(settings.SERVICES_MINIO_HOST,
                 access_key=settings.SERVICES_MINIO_ACCESS_KEY,
                 secret_key=settings.SERVICES_MINIO_SECRET_KEY,
                 secure=False,
                 region='mblocks'
                 )

def get_settings():
    return settings
