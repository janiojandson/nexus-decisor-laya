# app/main.py
"""
🚀 LAYA — Sistema 1 do Nexus (FastAPI + Quant Fast-Path sub-5ms)
Endpoints:
- POST /v1/systemone (Governança Quantitativa e Triagem Nexus)
- POST /decide (Compatibilidade legado)
- GET /health, GET /stats
"""

import secrets
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .config import PORT, HOST, LAYA_API_KEY
from .routes.system_one import router as system_one_router
from .routes.decide import router as decide_router
from .routes.health import router as health_router

# Configuração do rate limiter com fallback seguro
limiter = Limiter(key_func=get_remote_address, default_limits=["300/minute"])

app = FastAPI(
    title="Nexus Decisor Laya",
    description="Sistema 1 de Decisão Rápida e Governança Quantitativa",
    version="2.3.0",
)

# Registra rate limiter no app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS aberto para malha interna e dashboards autorizados
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Bypass para health checks
    if request.url.path in ("/health", "/stats", "/docs", "/openapi.json"):
        return await call_next(request)

    if LAYA_API_KEY:
        key = request.headers.get("x-laya-key") or request.headers.get("authorization", "").replace("Bearer ", "")
        # Comparação de tempo constante para prevenir timing attacks
        if not secrets.compare_digest(key or "", LAYA_API_KEY or ""):
            return Response(content='{"success": false, "error": "Acesso negado."}', status_code=401, media_type="application/json")

    return await call_next(request)


# Inclusão das rotas
app.include_router(system_one_router)
app.include_router(decide_router)
app.include_router(health_router)


if __name__ == "__main__":
    import uvicorn
    print(f"🧠 [LAYA] Sistema 1 ativo na porta {PORT} — decisão determinística sub-5ms.")
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False, access_log=False)
