# app/models/schemas.py
from typing import Dict, Any, Optional, Union, List
from pydantic import BaseModel, Field, model_validator


class MicrostructureData(BaseModel):
    bestBid: float = 0.0
    bestAsk: float = 0.0
    spreadBps: float = 0.0
    depthImbalanceRatio: float = 1.0
    whaleWallDetected: bool = False
    whaleWallDistancePct: float = 0.0
    whaleWallVolumeUsd: float = 0.0
    wall_persistence_ms: int = 0


class MacroData(BaseModel):
    regime: str = "NEUTRAL"
    circuitBreakerActive: bool = False
    powerMultiplier: float = 1.0
    btcFundingRate: float = 0.0001


class RiskData(BaseModel):
    accountEquity: float = 10000.0
    currentRiskAggregatePct: float = 0.0
    proposedRiskPct: float = 0.01
    atr14: float = 0.0


class SystemOneRequest(BaseModel):
    stateVersion: Optional[str] = "2.0"
    requestId: Optional[str] = None
    timestamp: Optional[int] = None
    symbol: Optional[str] = None
    side: Optional[str] = None
    currentPrice: Optional[float] = None
    proposedStopLoss: Optional[float] = None
    proposedTakeProfit: Optional[float] = None
    delta_stop_bps: Optional[float] = None
    signalSource: Optional[str] = None
    microstructure: Optional[Union[MicrostructureData, Dict[str, Any]]] = None
    macro: Optional[Union[MacroData, Dict[str, Any]]] = None
    risk: Optional[Union[RiskData, Dict[str, Any]]] = None
    state: Optional[Dict[str, Any]] = None
    questions: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def validate_nested_quant_state(self):
        state = self.state or {}
        is_quant = state.get("origem") == "mercado_financeiro" or "microstructure" in state or "action" in (self.questions or {})
        if not is_quant:
            return self

        for key in ("currentPrice", "proposedStopLoss", "proposedTakeProfit", "delta_stop_bps", "currentR"):
            value = state.get(key)
            if value is not None:
                try:
                    float(value)
                except (TypeError, ValueError):
                    raise ValueError(f"state.{key} deve ser numérico")

        side = state.get("side")
        if side is not None and str(side).upper() not in ("BUY", "SELL"):
            raise ValueError("state.side deve ser BUY ou SELL")
        return self


class SystemOneAnswer(BaseModel):
    choice: str
    verdict: Optional[str] = None
    rationale: Optional[str] = None
    confidence: float = 0.95
    answer_confidence: Optional[float] = 0.95


class SystemOneRouting(BaseModel):
    model: str = "laya-v2-quant-fastpath"
    latency_ms: float = 0.0


class SystemOneResponse(BaseModel):
    success: bool = True
    answers: Dict[str, Any] = Field(default_factory=dict)
    verdict: Optional[str] = None
    rationale_code: Optional[str] = None
    routing: SystemOneRouting = Field(default_factory=SystemOneRouting)


class DecideRequest(BaseModel):
    state: Dict[str, Any]
    questions: Optional[Dict[str, Any]] = None


class DecideResponse(BaseModel):
    success: bool = True
    answers: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)
