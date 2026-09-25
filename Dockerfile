# LAYA REAL — Motor de Decisão System 1 (NandhaKishorM/laya)
# Python + PyTorch CPU · endpoint Jev-compatible POST /v1/systemone
FROM python:3.11-slim

WORKDIR /app

# Dependências do laya-serve (FastAPI + uvicorn + transformers + torch CPU)
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch \
    && pip install --no-cache-dir "laya[serve]"

# Cache dos checkpoints em volume persistente (evita re-download de ~1GB a cada deploy)
ENV HF_HOME=/data/hf
ENV LAYA_HOST=0.0.0.0
ENV LAYA_PORT=8000
ENV LAYA_DEVICE=cpu
ENV LAYA_THREADS=2

EXPOSE 8000

CMD ["laya-serve"]
