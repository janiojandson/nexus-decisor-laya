# app/routes/system_one.py
import time
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
from ..engine.quant_rules import evaluate_quant_rules
from ..engine.nlp_triage import classificar_triage_cerebro

router = APIRouter()


@router.post("/v1/systemone")
async def handle_system_one(request: Request):
    t0 = time.perf_counter()
    
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="request body must be a valid JSON object")

    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="request body must be an object")

    # Verifica se há o bloco questions ou state
    state = data.get("state") or {}
    questions = data.get("questions") or {}
    origem = state.get("origem") or data.get("origem") or ""

    # =========================================================================
    # CASO A: Requisição Quantitativa do Mercado Financeiro
    # (identificada por questions.action, state.microstructure ou origem == 'mercado_financeiro')
    # =========================================================================
    if (
        "action" in questions
        or "microstructure" in data
        or "microstructure" in state
        or origem == "mercado_financeiro"
        or "delta_stop_bps" in data
    ):
        choice, verdict, rationale, confidence = evaluate_quant_rules(data)
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)

        return {
            "success": True,
            "answers": {
                "action": {
                    "choice": choice,
                    "verdict": verdict,
                    "rationale": rationale,
                    "confidence": confidence,
                    "answer_confidence": confidence,
                }
            },
            "verdict": verdict,
            "rationale_code": rationale,
            "routing": {
                "model": "laya-v2-quant-fastpath",
                "latency_ms": latency_ms,
            },
        }

    # =========================================================================
    # CASO B: Triagem de Linguagem Natural (Nexus-Cérebro / Telegram / Terminal)
    # (identificada por questions com destino/risco/precisa_llm ou state.body)
    # =========================================================================
    body = state.get("body") or state.get("mensagem") or data.get("body") or data.get("mensagem") or ""
    triage_result = classificar_triage_cerebro(origem, body)
    
    # Filtra apenas as perguntas requisitadas pelo cliente
    answers = {}
    if questions and isinstance(questions, dict):
        for q_key in questions.keys():
            if q_key in triage_result:
                answers[q_key] = triage_result[q_key]
    
    if not answers:
        answers = triage_result

    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    return {
        "success": True,
        "answers": answers,
        "routing": {
            "model": "laya-v2-nlp-fastpath",
            "latency_ms": latency_ms,
        },
    }
