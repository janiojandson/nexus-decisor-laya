# app/routes/__init__.py
from .system_one import router as system_one_router
from .decide import router as decide_router
from .health import router as health_router

__all__ = ["system_one_router", "decide_router", "health_router"]
