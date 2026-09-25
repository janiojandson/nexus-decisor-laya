# AGENTE: Laya — Decisor do Sistema 1
**Módulo:** nexus-decisor-laya
**Versão do Agente:** 2.0.0 (Laya real — NandhaKishorM/laya)
**Porta do Serviço:** 8080 (Railway) · 8000 em dev local
**Papel na arquitetura:** Camada 1 — portão barato de triagem (decide SE e PARA ONDE, antes de qualquer LLM)

## 🎯 1. MISSÃO E ESCOPO

- **Objetivo Primário:** Triar toda entrada do ecossistema Nexus com zero custo de tokens: destino (choice), risco (score) e necessidade de LLM (noul) em uma única passagem forward.
- **Escopo Permitido:** apenas `POST /v1/systemone` (protocolo Jev-compatible), `GET /health`. Sem estado persistente além do cache de checkpoints.

**Motor:** transformer não-autoregressivo (mmBERT multilingual 322M para pt-BR), confiança calibrada por RLCD, fine-tunable para o domínio Nexus.

## 🔌 2. ENDPOINTS E CONTRATO

| Rota | Método | Função |
|---|---|---|
| `/v1/systemone` | POST | Decisão tipada (protocolo Jev) |
| `/health` | GET | Health check |

**Payload (contrato oficial Laya/Jev):**
```json
{
  "state": { "body": "texto da mensagem" },
  "questions": {
    "destino":     { "type": "choice", "instructions": "Para qual setor?", "criteria": { "memoria": "...", "sistema": "...", "github": "..." } },
    "risco":       { "type": "score", "instructions": "Risco 0-2", "criteria": ["leitura", "alteração", "destruição"] },
    "precisa_llm": { "type": "noul", "instructions": "Exige síntese em linguagem natural?" }
  }
}
```

**Resposta:** `answers.<pergunta>.{choice|score|noul}` + `confidence` + `answer_confidence` (probabilidade calibrada da resposta — usar ESTA para gating).

## ⚙️ 3. CONFIGURAÇÃO (env Railway)

| Var | Valor | Função |
|---|---|---|
| `LAYA_PORT` | 8080 (Railway) · 8000 local | Porta do serviço |
| `LAYA_DEVICE` | cpu | Inferência CPU (~200-400ms) |
| `LAYA_PRELOAD` | 1 | Checkpoints pré-carregados (sem cold start por idioma) |
| `LAYA_MODELS` | multilingual | Só o checkpoint multilingual (pt-BR) — economiza RAM |
| `LAYA_THREADS` | 2 | Threads de inferência |
| `LAYA_API_KEY` | (opcional) | Se setada, exige header `x-laya-key` |
| `HF_HOME` | /data/hf | Cache de checkpoints no volume persistente |

## 💻 USO LOCAL (terminal / IDE)

CLI na pasta do projeto: `node tools/laya-local.js "mensagem ou comando para triagem"`.
Env `LAYA_URL` (default: domínio público do Railway; `http://localhost:8000` para Laya local).

## 🛡️ 4. REGRAS DO ECOSSISTEMA

- Roda apenas na Railway Private Mesh (`nexus-decisor-laya.railway.internal:8000`) — sem domínio público.
- NUNCA executa nada — só decide. Execução é das camadas 2-4.
- Cérebro consulta com timeout 1.5s → falha = fluxo LLM normal (degradação graciosa).
- Limiar recomendado: `answer_confidence >= 0.88` age direto; `< 0.70` valida com `auto/best-fast`.
- Fine-tuning futuro: notebook Kaggle 2xT4 no repo oficial eleva acurácia de 0.36 → 0.77 no domínio.

## 📦 5. ESTRUTURA

```
Dockerfile                    — imagem python:3.11-slim + laya[serve] (torch CPU)
arquivo-standin-regras/src/   — stand-in Node de regras (referência/fallback emergencial)
```
