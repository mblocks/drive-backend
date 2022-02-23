# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import routers, backgrounds

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(routers.welcome, tags=["welcome"])
app.include_router(routers.webhooks, tags=["webhooks"], prefix="/webhooks")


@app.on_event("startup")
async def startup_event():
    backgrounds.init_minio()
