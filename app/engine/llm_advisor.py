# app/engine/llm_advisor.py
"""
Módulo de Fallback LLM / OmniRoute para Casos Ambíguos.
Configurado com System Prompt institucional balanceado (sem viés de aversão excessiva).
"""

import httpx
from typing import Dict, Any, Optional
from ..config import OMNIROUTE_URL, NEXUS_API_KEY


SYSTEM_PROMPT_QUANT = """
Você é a LAYA (Sistema 1 do Nexus), uma inteligência de alta velocidade e precisão para governança de trading quantitativo e microestrutura de mercado (Order Flow).

DIRETRIZES DE DECISÃO:
1. Quando a microestrutura institucional confirmar ABSORÇÃO PASSIVA ou DESBALANCEAMENTO DE LIVRO e os parâmetros de risco (spread <= 5 bps, delta_stop >= 55 bps) estiverem satisfeitos, APROVE A ENTRADA (choice: "AUTHORIZE"). NÃO vete por aversão genérica a volatilidade de mercado.
2. VETE (choice: "VETO") única e exclusivamente quando houver quebra objetiva de regras: spread tóxico (> 5.0 bps), circuit breaker do sentinel ativo, regime de dump descontrolado com ordem de compra, ou spoofing comprovado.
3. Responda estritamente com o veredito ("AUTHORIZE", "VETO", "HOLD", "CLOSE_NOW", "EARLY_HARVEST_CLOSE") e a justificativa técnica sucinta.
"""


async def consultar_omniroute_fallback(context_desc: str, question: str) -> Optional[Dict[str, Any]]:
    """Consulta o OmniRoute se configurado e disponível."""
    if not OMNIROUTE_URL:
        return None

    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            headers = {"Content-Type": "application/json"}
            if NEXUS_API_KEY:
                headers["Authorization"] = f"Bearer {NEXUS_API_KEY}"

            payload = {
                "model": "auto/best-fast",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT_QUANT},
                    {"role": "user", "content": f"Contexto: {context_desc}\nPergunta: {question}"}
                ],
                "temperature": 0.1,
                "max_tokens": 100
            }
            res = await client.post(f"{OMNIROUTE_URL}/v1/chat/completions", json=payload, headers=headers)
            if res.status_code == 200:
                data = res.json()
                content = data["choices"][0]["message"]["content"].strip().upper()
                choice = "AUTHORIZE" if "AUTHORIZE" in content or "APPROVE" in content else "VETO"
                return {"choice": choice, "rationale": "LLM_BALANCED_INFERENCE"}
    except Exception:
        pass
    return None
