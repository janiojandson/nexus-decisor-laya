# app/routes/decide.py
import time
from fastapi import APIRouter, Request, HTTPException
from ..engine.nlp_triage import classificar_triage_cerebro

router = APIRouter()

stats_decide = {
    "total": 0,
    "latencia_media_ms": 0.0,
}


@router.post("/decide")
async def handle_decide(request: Request):
    t0 = time.perf_counter()
    
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    state = data.get("state") or {}
    mensagem = state.get("mensagem") or state.get("body") or ""
    origem = state.get("origem") or "desconhecida"

    if not mensagem:
        raise HTTPException(
            status_code=400,
            detail="Payload inválido: informe { state: { origem, mensagem }, questions: { destino, risco, precisa_llm } }",
        )

    triage = classificar_triage_cerebro(origem, mensagem)
    questions = data.get("questions") or {}

    answers = {}
    if questions and isinstance(questions, dict):
        for q_key in questions.keys():
            if q_key in triage:
                answers[q_key] = triage[q_key]

    if not answers:
        answers = triage

    duracao_ms = round((time.perf_counter() - t0) * 1000, 2)

    stats_decide["total"] += 1
    total = stats_decide["total"]
    stats_decide["latencia_media_ms"] = round(
        ((stats_decide["latencia_media_ms"] * (total - 1)) + duracao_ms) / total, 2
    )

    return {
        "success": True,
        "answers": answers,
        "meta": {
            "origem": origem,
            "duracao_ms": duracao_ms,
            "motor": "laya-v2-hybrid-fastpath",
        },
    }
