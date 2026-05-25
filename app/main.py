"""
SignalFlow FastAPI 服务入口。

启动方式：
    cd <project_root>
    pip install -r app/requirements.txt
    uvicorn app.main:app --reload --port 8080
"""

from fastapi import FastAPI
from app.search_api import router

app = FastAPI(
    title="SignalFlow API",
    description="自动化 AI 信息筛选与简报系统 — 本地检索服务",
    version="0.3.0",
)

app.include_router(router)
