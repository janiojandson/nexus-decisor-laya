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
    
    # Intent / Contexto
    body = str(state.get("body") or "")
    intent_group = "PRE_ENTRY"
    intent_subgroup = "NEW_OPPORTUNITY"
    current_r = 0.0
    
    # Validação crítica: preços devem ser estritamente positivos
    if current_price <= 0 or proposed_stop <= 0:
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
    
    # Se delta_stop_bps veio zerado mas temos preços, calcula
    if delta_stop_bps <= 0:
        delta_stop_bps = round((abs(current_price - proposed_stop) / current_price) * 10000, 2)
        # Valida após cálculo
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
            
    # Extrai currentR do body se existir
    if "PnL_R:" in body:
        try:
            parts = body.split("PnL_R:")[1].split("R")[0].strip()
            current_r = float(parts)
        except Exception:
            pass

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
        # Se houver estrutura de reversão confirmada no body
        if "Sweep" in p["body"] or "rejeição" in p["body"] or "sweep" in p["body"].lower():
            return "OVERRIDE_COOLDOWN", "OVERRIDE_COOLDOWN", "COOLDOWN_PARDON_SWEEP_RECLAIM", 0.95
        return "VETO", "VETO", "COOLDOWN_MAINTAINED", 0.90

    # =========================================================================
    # 2. TRATAMENTO DE INTENÇÃO: POSITION_LIFECYCLE
    # =========================================================================
    if intent_group == "POSITION_LIFECYCLE":
        if intent_subgroup == "DEFENSE_CONTRARIAN_FLOW":
            # Se baleia contrária confirmada com trade no negativo
            if p["current_r"] < -0.3:
                return "CLOSE_NOW", "CLOSE_NOW", "DEFENSE_CONTRARIAN_EXIT", 0.96
            return "HOLD", "HOLD", "HOLD_NORMAL_OSCILLATION", 0.90

        if intent_subgroup == "RUNNER_EVALUATION":
            # Se atingiu >= 1.2R e há exaustão
            if p["current_r"] >= 1.2:
                return "EARLY_HARVEST_CLOSE", "EARLY_HARVEST_CLOSE", "EARLY_HARVEST_TOP_EXHAUSTION", 0.95
            return "HOLD", "HOLD", "RUNNER_EXTENDING", 0.90

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
