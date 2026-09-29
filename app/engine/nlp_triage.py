# app/engine/nlp_triage.py
"""
Motor de Triagem de Linguagem Natural para o Nexus-Cérebro.
Executa classificação rápida de destino, risco operacional e necessidade de LLM em < 2ms.
"""

import re
import unicodedata
from typing import Dict, Any


VOCABULARIO_DESTINOS = {
    "memoria": {
        "palavras": [
            "memoria", "memória", "lembra", "lembre", "historico", "histórico", "ontem", "anteontem",
            "pesquisa anterior", "ultima pesquisa", "última pesquisa", "hipocampo", "obsidian", "nota",
            "notas", "cofre", "aprendeu", "aprendizado", "sabe sobre", "o que descobrimos", "insight"
        ],
        "peso": 1.0,
    },
    "sistema": {
        "palavras": [
            "status", "porta", "portas", "servico", "serviço", "shell", "comando", "arquivo", "arquivos",
            "disco", "processo", "log", "logs", "saude", "saúde", "uptime", "memoria do sistema", "cpu",
            "versao", "versão", "diagnostico", "diagnóstico", "heartbeat", "membros online"
        ],
        "peso": 1.0,
    },
    "github": {
        "palavras": [
            "repositorio", "repositório", "repo", "commit", "pull request", "pr ", "clone", "clonar",
            "github", "branch", "merge", "issues", "fork", "star", "subir codigo", "subir código",
            "push", "deploy no railway", "lancar no railway", "lançar no railway"
        ],
        "peso": 1.0,
    },
    "mercado_financeiro": {
        "palavras": [
            "candle", "candles", "trading", "bybit", "mercado", "preco", "preço", "ativo", "ativos",
            "klines", "fluxo", "whale", "absorção", "absorcao", "book imbalance", "timeframe", "ordem",
            "b3", "binance", "bitcoin", "btc", "cripto", "acao", "ação", "acoes", "ações", "sol", "eth"
        ],
        "peso": 1.0,
    },
    "licitacoes": {
        "palavras": [
            "licitacao", "licitação", "licitacoes", "licitações", "edital", "editais", "pncp",
            "comprasnet", "proposta comercial", "pregao", "pregão", "orgao publico", "órgão público",
            "contratação publica", "contratacao publica"
        ],
        "peso": 1.0,
    },
    "buscador": {
        "palavras": [
            "lead", "leads", "prospeccao", "prospecção", "buscar cliente", "clientes potenciais",
            "google maps", "cnpj", "instagram", "tiktok", "gerar lead", "lista de empresas", "contato"
        ],
        "peso": 1.0,
    },
    "comunicacao": {
        "palavras": [
            "whatsapp", "telegram", "mensagem", "mensagens", "chatbot", "bot", "enviar para",
            "broadcast", "fila de mensagem", "baileys", "atendimento"
        ],
        "peso": 1.0,
    },
    "descarte": {
        "palavras": [
            "oi", "ola", "olá", "bom dia", "boa tarde", "boa noite", "valeu", "vlw", "ok",
            "obrigado", "obrigada", "tchau", "beleza", "show", "top", "👍", "❤️"
        ],
        "peso": 0.8,
    },
}

GATILHOS_RISCO = [
    (re.compile(r"\b(deletar|apagar|remover|deletar tudo|dropar|drop|formatar|limpar tudo)\b", re.I), 1.9),
    (re.compile(r"\b(pagar|pagamento|comprar|assinatura|cartao|cartão|transacao|transação|pix|boleto|investir)\b", re.I), 1.7),
    (re.compile(r"\b(deploy em producao|deploy em produção|producao agora|produção agora|force push|reset --hard)\b", re.I), 1.6),
    (re.compile(r"\b(criar|alterar|modificar|editar|atualizar|renomear|mover|enviar|commit|push|publicar)\b", re.I), 0.9),
    (re.compile(r"\b(status|listar|mostrar|ver|ler|consultar|buscar|pesquisar|quanto|quantos|qual|quando)\b", re.I), 0.2),
]

GATILHOS_LLM = [
    re.compile(r"\b(analis\w+|resum\w+|escrev\w+|redig\w+|cri\w+ um|criar um|elabor\w+|compar\w+|avali\w+|sintetiz\w+)\b", re.I),
    re.compile(r"\b(como|por que|porque|explique|explicar|o que acha|sua opiniao|sua opinião|sugest\w+|recomend\w+)\b", re.I),
    re.compile(r"\b(plano|estrategia|estratégia|passo a passo|ideias|brainstorm|monetiz\w+|pitch)\b", re.I),
]

GATILHOS_DIRETO = [
    re.compile(r"^(\/|!)?(status|saude|saúde|health|versao|versão|uptime|membros|ferramentas|ajuda|help)\b", re.I),
    re.compile(r"^(\/|!)?(oi|ola|olá|bom dia|boa tarde|boa noite)\b", re.I),
]


def normalizar(texto: str) -> str:
    texto_str = str(texto or "").lower()
    return unicodedata.normalize("NFD", texto_str).encode("ascii", "ignore").decode("utf-8")


def classificar_destino(mensagem: str) -> Dict[str, Any]:
    msg_raw = normalizar(mensagem)
    msg_spaced = f" {msg_raw} "
    scores = {}

    for destino, cfg in VOCABULARIO_DESTINOS.items():
        score = 0.0
        for palavra in cfg["palavras"]:
            p = normalizar(palavra)
            if f" {p} " in msg_spaced:
                score += 1.0 * cfg["peso"]
            elif p in msg_raw:
                score += 0.6 * cfg["peso"]
        scores[destino] = score

    sorted_destinos = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    melhor, score_top = sorted_destinos[0]
    segundo, score_vice = sorted_destinos[1] if len(sorted_destinos) > 1 else (None, 0.0)

    if score_top == 0:
        return {"choice": "descarte", "confidence": 0.4, "answer_confidence": 0.4}

    forca = min(score_top / 3.0, 1.0)
    margem = (score_top - score_vice) / score_top if score_top > 0 else 0.0
    confidence = round(min(0.40 + forca * 0.40 + margem * 0.20, 0.98), 2)

    return {"choice": melhor, "confidence": confidence, "answer_confidence": confidence}


def classificar_risco(mensagem: str) -> Dict[str, Any]:
    risco = 0.2
    for pattern, peso in GATILHOS_RISCO:
        if pattern.search(mensagem):
            risco = max(risco, peso)
    return {"score": round(risco, 2), "confidence": 0.92}


def classificar_precisa_llm(mensagem: str, destino: str) -> Dict[str, Any]:
    msg = str(mensagem or "").strip()

    if any(p.search(msg) for p in GATILHOS_DIRETO) and len(msg) < 60:
        return {"noul": 0.0, "confidence": 0.95}

    if destino == "descarte" and len(msg) < 40:
        return {"noul": 0.0, "confidence": 0.95}

    if any(p.search(msg) for p in GATILHOS_LLM):
        return {"noul": 1.0, "confidence": 0.94}

    if len(msg) > 200:
        return {"noul": 1.0, "confidence": 0.88}

    if "?" in msg:
        return {"noul": 0.8, "confidence": 0.80}

    return {"noul": 0.0, "confidence": 0.75}


def classificar_triage_cerebro(origem: str, mensagem: str) -> Dict[str, Any]:
    destino = classificar_destino(mensagem)
    risco = classificar_risco(mensagem)
    precisa_llm = classificar_precisa_llm(mensagem, destino["choice"])

    # Se risco for elevado, força necessidade de LLM
    if risco["score"] > 1.4:
        precisa_llm["noul"] = 1.0
        precisa_llm["confidence"] = 0.95

    return {
        "destino": destino,
        "risco": risco,
        "precisa_llm": precisa_llm,
    }
