# app/config.py
import os

PORT = int(os.getenv("PORT", os.getenv("LAYA_PORT", "8000")))
HOST = os.getenv("LAYA_HOST", "0.0.0.0")
LAYA_API_KEY = os.getenv("LAYA_API_KEY", None)
OMNIROUTE_URL = os.getenv("OMNIROUTE_URL", "http://nexus-omniroute.railway.internal:8080")
NEXUS_API_KEY = os.getenv("NEXUS_API_KEY", "")
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

# Limites de governança quantitativa
MAX_SAFE_SPREAD_BPS = 5.0
MIN_DELTA_STOP_BPS = 55.0
MAX_PORTFOLIO_RISK_PCT = 0.05  # 5%
MIN_WALL_PERSISTENCE_MS = 1500  # 1.5s
