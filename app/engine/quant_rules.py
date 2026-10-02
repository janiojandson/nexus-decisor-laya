# app/engine/quant_rules.py
"""
Motor de Decisão Quantitativa Determinística (Fast-Path < 5ms).
Implementa as Regras V1 a V12 da governança Laya v2.
"""

from typing import Dict, Any, Tuple
from ..config import (
    MAX_SAFE_SPREAD_BPS,
    MIN_DELTA_STOP_BPS,
    MAX_PORTFOLIO_RISK_PCT,
    MIN_WALL_PERSISTENCE_MS,
)


def extract_quant_payload(req_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extrai campos quantitativos tanto do root quanto do bloco aninhado state."""
    state = req_data.get("state") or {}
    
    # Extração de campos base
    symbol = req_data.get("symbol") or state.get("symbol") or "UNKNOWN"
    side = req_data.get("side") or state.get("side") or "BUY"
    current_price = float(req_data.get("currentPrice") or state.get("currentPrice") or 0.0)
    proposed_stop = float(req_data.get("proposedStopLoss") or state.get("proposedStopLoss") or 0.0)
    proposed_tp = float(req_data.get("proposedTakeProfit") or state.get("proposedTakeProfit") or 0.0)
    delta_stop_bps = float(req_data.get("delta_stop_bps") or state.get("delta_stop_bps") or 0.0)
    signal_source = req_data.get("signalSource") or state.get("signalSource") or "FLOW_SIGNAL"
    
    # Bloco de microestrutura
    micro = req_data.get("microstructure") or state.get("microstructure") or {}
    spread_bps = float(micro.get("spreadBps", 0.0))
    depth_imbalance = float(micro.get("depthImbalanceRatio", 1.0))
    whale_wall_detected = bool(micro.get("whaleWallDetected", False))
    wall_persistence_ms = int(micro.get("wall_persistence_ms", 0))
    
    # Bloco macro
    macro = req_data.get("macro") or state.get("macro") or {}
    regime = macro.get("regime", "NEUTRAL")
    circuit_breaker = bool(macro.get("circuitBreakerActive", False))
    power_multiplier = float(macro.get("powerMultiplier", 1.0))
    
    # Bloco de risco
    risk = req_data.get("risk") or state.get("risk") or {}
    account_equity = float(risk.get("accountEquity", 10000.0))
    curr_risk_agg =float(risk.get("currentRiskAggregatePct", 0.0))
    prop_risk_pct = float(risk.get("proposedRiskPct", 0.01))
    
    # Intent / Contexto — campos estruturados têm precedência sobre texto livre.
    body = str(state.get("body") or "")
    intent_group = str(state.get("intentGroup") or req_data.get("intentGroup") or "PRE_ENTRY").upper()
    intent_subgroup = str(state.get("intentSubgroup") or req_data.get("intentSubgroup") or "NEW_OPPORTUNITY").upper()
    evidence = state.get("evidence") or req_data.get("evidence") or {}
    current_r_raw = state.get("currentR", req_data.get("currentR", 0.0))
    try:
        current_r = float(current_r_raw or 0.0)
    except (TypeError, ValueError):
        current_r = 0.0

    # Compatibilidade com clientes antigos que ainda codificam intenção no body.
    if not state.get("intentGroup") and not req_data.get("intentGroup"):
        if "COOLDOWN_AUDIT" in body or "COOLDOWN" in body:
            intent_group = "COOLDOWN_AUDIT"
            intent_subgroup = "LIQUIDITY_SWEEP_REENTRY"
        elif "POSITION_LIFECYCLE" in body:
            intent_group = "POSITION_LIFECYCLE"
            if "DEFENSE_CONTRARIAN_FLOW" in body:
                intent_subgroup = "DEFENSE_CONTRARIAN_FLOW"
            elif "RUNNER_EVALUATION" in body:
                intent_subgroup = "RUNNER_EVALUATION"
            elif "SCALE_IN_REQUEST" in body:
                intent_subgroup = "SCALE_IN_REQUEST"

    # Compatibilidade: extrai currentR do texto somente se não veio estruturado.
    if not state.get("currentR") and req_data.get("currentR") is None and "PnL_R:" in body:
        try:
            parts = body.split("PnL_R:")[1].split("R")[0].strip()
            current_r = float(parts)
        except Exception:
            pass

    # currentPrice é obrigatório em todas as decisões financeiras.
    # Stop é obrigatório apenas quando há nova exposição (PRE_ENTRY / SCALE_IN).
    requires_stop = intent_group == "PRE_ENTRY" or intent_subgroup == "SCALE_IN_REQUEST"
    if current_price <= 0 or (requires_stop and proposed_stop <= 0):
        return {
            "symbol": symbol,
            "side": side.upper(),
            "current_price": current_price,
            "proposed_stop": proposed_stop,
            "proposed_tp": proposed_tp,
            "delta_stop_bps": 0.0,
            "signal_source": signal_source,
            "spread_bps": spread_bps,
            "depth_imbalance": depth_imbalance,
            "whale_wall_detected": whale_wall_detected,
            "wall_persistence_ms": wall_persistence_ms,
            "regime": regime.upper(),
            "circuit_breaker": circuit_breaker,
            "power_multiplier": power_multiplier,
            "account_equity": account_equity,
            "curr_risk_agg": curr_risk_agg,
            "prop_risk_pct": prop_risk_pct,
            "intent_group": intent_group,
            "intent_subgroup": "INVALID_PAYLOAD",
            "current_r": current_r,
            "body": body,
            "_validation_error": "V00_INVALID_PRICE_OR_STOP"
        }
    
    # Delta de stop só é requisito para ações que criam/aumentam exposição.
    if requires_stop and delta_stop_bps <= 0:
        delta_stop_bps = round((abs(current_price - proposed_stop) / current_price) * 10000, 2)
        if delta_stop_bps < MIN_DELTA_STOP_BPS:
            return {
                "symbol": symbol,
                "side": side.upper(),
                "current_price": current_price,
                "proposed_stop": proposed_stop,
                "proposed_tp": proposed_tp,
                "delta_stop_bps": delta_stop_bps,
                "signal_source": signal_source,
                "spread_bps": spread_bps,
                "depth_imbalance": depth_imbalance,
                "whale_wall_detected": whale_wall_detected,
                "wall_persistence_ms": wall_persistence_ms,
                "regime": regime.upper(),
                "circuit_breaker": circuit_breaker,
                "power_multiplier": power_multiplier,
                "account_equity": account_equity,
                "curr_risk_agg": curr_risk_agg,
                "prop_risk_pct": prop_risk_pct,
                "intent_group": intent_group,
                "intent_subgroup": "INVALID_PAYLOAD",
                "current_r": current_r,
                "body": body,
                "_validation_error": "V12_INSUFFICIENT_DELTA_CALCULATED"
            }
    
    return {
        "symbol": symbol,
        "side": side.upper(),
        "current_price": current_price,
        "proposed_stop": proposed_stop,
        "proposed_tp": proposed_tp,
        "delta_stop_bps": delta_stop_bps,
        "signal_source": signal_source,
        "spread_bps": spread_bps,
        "depth_imbalance": depth_imbalance,
        "whale_wall_detected": whale_wall_detected,
        "wall_persistence_ms": wall_persistence_ms,
        "regime": regime.upper(),
        "circuit_breaker": circuit_breaker,
        "power_multiplier": power_multiplier,
        "account_equity": account_equity,
        "curr_risk_agg": curr_risk_agg,
        "prop_risk_pct": prop_risk_pct,
        "intent_group": intent_group,
        "intent_subgroup": intent_subgroup,
        "current_r": current_r,
        "evidence": evidence,
        "body": body,
    }


def evaluate_quant_rules(payload: Dict[str, Any]) -> Tuple[str, str, str, float]:
    """
    Avalia deterministicamente o sinal quantitativo.
    Retorna: (choice, verdict, rationale_code, confidence)
    
    Vereditos possíveis:
    - APPROVE_PASSIVE / AUTHORIZE (Maker)
    - APPROVE_AGGRESSIVE / AUTHORIZE (Taker)
    - VETO / VETO
    - OVERRIDE_COOLDOWN / OVERRIDE_COOLDOWN
    - CLOSE_NOW / CLOSE_NOW
    - EARLY_HARVEST_CLOSE / EARLY_HARVEST_CLOSE
    - HOLD / HOLD
    """
    p = extract_quant_payload(payload)
    
    # Validação crítica: aborta se preços inválidos ou stop insuficiente
    if "_validation_error" in p:
        return "VETO", "VETO", p["_validation_error"], 0.99
    
    intent_group = p["intent_group"]
    intent_subgroup = p["intent_subgroup"]

    # =========================================================================
    # 1. TRATAMENTO DE INTENÇÃO: COOLDOWN_AUDIT
    # =========================================================================
    if intent_group == "COOLDOWN_AUDIT":
        evidence = p.get("evidence") or {}
        sweep_confirmed = bool(evidence.get("liquiditySweepConfirmed", False))
        rejection_confirmed = bool(evidence.get("rejectionConfirmed", False))
        if sweep_confirmed and rejection_confirmed:
            return "OVERRIDE_COOLDOWN", "OVERRIDE_COOLDOWN", "COOLDOWN_PARDON_SWEEP_RECLAIM", 0.95
        return "VETO", "VETO", "COOLDOWN_MAINTAINED_NO_CONFIRMED_EVIDENCE", 0.95

    # =========================================================================
    # 2. TRATAMENTO DE INTENÇÃO: POSITION_LIFECYCLE
    # =========================================================================
    if intent_group == "POSITION_LIFECYCLE":
        evidence = p.get("evidence") or {}

        if intent_subgroup == "DEFENSE_CONTRARIAN_FLOW":
            contrarian_confirmed = bool(evidence.get("contrarianFlowConfirmed", False))
            if contrarian_confirmed and p["current_r"] < -0.3:
                return "CLOSE_NOW", "CLOSE_NOW", "DEFENSE_CONTRARIAN_EXIT", 0.96
            return "HOLD", "HOLD", "HOLD_NO_CONFIRMED_CONTRARIAN_FLOW", 0.95

        if intent_subgroup == "RUNNER_EVALUATION":
            exhaustion_confirmed = bool(evidence.get("exhaustionConfirmed", False))
            if exhaustion_confirmed and p["current_r"] >= 1.2:
                return "EARLY_HARVEST_CLOSE", "EARLY_HARVEST_CLOSE", "EARLY_HARVEST_TOP_EXHAUSTION", 0.95
            return "HOLD", "HOLD", "RUNNER_EXTENDING_NO_CONFIRMED_EXHAUSTION", 0.95

        if intent_subgroup == "SCALE_IN_REQUEST":
            if p["current_r"] >= 1.2 and (p["curr_risk_agg"] + p["prop_risk_pct"] <= MAX_PORTFOLIO_RISK_PCT):
                return "AUTHORIZE", "AUTHORIZE_SCALE_IN", "SCALE_IN_AUTHORIZED", 0.95
            return "VETO", "VETO", "SCALE_IN_RISK_REJECTED", 0.92

    # =========================================================================
    # 3. TRATAMENTO DE INTENÇÃO: PRE_ENTRY (MATRIZ DETERMINÍSTICA V1 A V12)
    # =========================================================================

    # V01: Spread Tóxico (> 5.0 bps)
    # Apenas se o spread for estritamente positivo (evita falsos positivos em book não hidratado)
    if p["spread_bps"] > MAX_SAFE_SPREAD_BPS:
        return "VETO", "VETO", "V01_TOXIC_SPREAD", 0.99

    # V02: Macro Sentinel Circuit Breaker
    if p["circuit_breaker"]:
        return "VETO", "VETO", "V02_CIRCUIT_BREAKER_ACTIVE", 0.99

    # V03: Veto Direcional em Bearish Dump para Compras
    if p["regime"] == "BEARISH_DUMP" and p["side"] == "BUY":
        return "VETO", "VETO", "V03_BEARISH_DUMP_BUY_VETO", 0.98

    # V12: Piso Estrutural de Stop (delta_stop_bps >= 55.0 bps)
    # Se delta_stop foi informado e está abaixo de 55 bps
    if 0 < p["delta_stop_bps"] < MIN_DELTA_STOP_BPS:
        return "VETO", "VETO", "V12_INSUFFICIENT_DELTA", 0.97

    # V05: Spoofing de Parede L2 (parede detectada com menos de 1500ms de vida)
    if p["whale_wall_detected"] and 0 < p["wall_persistence_ms"] < MIN_WALL_PERSISTENCE_MS:
        return "VETO", "VETO", "V05_SPOOFING_SUSPECT", 0.95

    # V06: Teto de Risco Portfólio Excedido (> 5%)
    if (p["curr_risk_agg"] + p["prop_risk_pct"]) > MAX_PORTFOLIO_RISK_PCT:
        return "VETO", "VETO", "V06_MAX_RISK_EXCEEDED", 0.98

    # V07: Fricção Excessiva em Stop Curto (spread > 3.0 bps com stop < 65 bps)
    if p["spread_bps"] > 3.0 and 0 < p["delta_stop_bps"] < 65.0:
        return "VETO", "VETO", "V07_EXCESSIVE_FRICTION_DRAG", 0.94

    # =========================================================================
    # 4. APROVAÇÃO DETERMINÍSTICA (FAST-PATH V08)
    # =========================================================================
    # Todas as salvaguardas passaram: APROVAÇÃO LIMPA
    source = p["signal_source"].upper()
    
    if "IMBALANCE" in source or p["depth_imbalance"] >= 2.5 or (p["side"] == "SELL" and p["depth_imbalance"] <= 0.4):
        # Desbalanceamento agudo -> Agressão imediata (Taker IOC)
        return "AUTHORIZE", "APPROVE_AGGRESSIVE", "V08_IMBALANCE_AGGRESSIVE_APPROVED", 0.98
    else:
        # Absorção passiva (ABSORPTION_BUY / ABSORPTION_SELL) -> Maker Post-Only
        return "AUTHORIZE", "APPROVE_PASSIVE", "V08_ABSORPTION_PASSIVE_APPROVED", 0.98
