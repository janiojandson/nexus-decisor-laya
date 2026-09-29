# app/routes/health.py
import time
from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter()
start_time = time.time()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "servico": "nexus-decisor-laya",
        "sistema": "1 (decisão rápida & quant fast-path)",
        "uptime_s": round(time.time() - start_time),
        "motor": "laya-v2-quant-fastpath",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/stats")
async def get_stats():
    return {
        "status": "online",
        "uptime_s": round(time.time() - start_time),
        "motor": "laya-v2-quant-fastpath",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
