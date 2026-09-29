# LAYA REAL v2.3 — Motor de Decisão System 1 & Quant Fast-Path
# Python 3.11 + FastAPI + Uvicorn · sub-5ms latência
FROM python:3.11-slim

WORKDIR /app

# Instala dependências leves (sem o peso de 1.5GB do PyTorch)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY . .

ENV LAYA_HOST=0.0.0.0
ENV LAYA_PORT=8000
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
