# -*- coding: utf-8 -*-
import uuid
from minio import Minio
from app.config import get_settings


settings = get_settings()
minio_client = Minio(settings.SERVICES_MINIO_HOST,
                 access_key=settings.SERVICES_MINIO_ACCESS_KEY,
                 secret_key=settings.SERVICES_MINIO_SECRET_KEY,
                 secure=False,
                 region='mblocks'
                 )

def get_uuid():
    return uuid.uuid4().hex

def get_minio_presigned_url(file_path, file_type):
    url = minio_client.presigned_get_object(settings.SERVICES_MINIO_BUCKET, file_path,response_headers={"response-content-type": file_type})
    if settings.SERVICES_MINIO_PROXY:
        find_index = url.index(settings.SERVICES_MINIO_HOST) + len(settings.SERVICES_MINIO_HOST)
        return settings.SERVICES_MINIO_PROXY + url[find_index:]
    return url
