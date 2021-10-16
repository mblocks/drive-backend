# -*- coding: utf-8 -*-
import os
import sys
from functools import lru_cache
from pydantic import BaseSettings

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# SQLite URI compatible
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'


class Settings(BaseSettings):
    FASTAPI_CONFIG: str = "development"
    APP_NAME: str = "Mblocks Drive"
    OPENAPI_PREFIX: str = ""
    SQLALCHEMY_DATABASE_URI: str = prefix + os.path.join(basedir, 'data.db')
    SQLALCHEMY_ECHO: bool = False

    SERVICES_MINIO_HOST: str = 'minio.local.com'
    SERVICES_MINIO_ACCESS_KEY: str = 'hello'
    SERVICES_MINIO_SECRET_KEY: str = 'helloworld'
    SERVICES_MINIO_BUCKET: str = 'drive'
    SERVICES_MINIO_PROXY: str = None
    
    class Config:
        case_sensitive: bool = True
        env_file: bool = ".env"

class Test(Settings):
    SQLALCHEMY_DATABASE_URI: str = prefix + os.path.join(basedir, 'test.db')


@lru_cache()
def get_settings():
    if os.getenv('FASTAPI_CONFIG') == 'test':
        return Test()
    return Settings()
