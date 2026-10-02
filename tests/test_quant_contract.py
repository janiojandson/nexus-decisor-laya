import unittest

from app.engine.quant_rules import evaluate_quant_rules
from app.models.schemas import SystemOneRequest
from pydantic import ValidationError


def payload(intent_group="PRE_ENTRY", intent_subgroup="NEW_OPPORTUNITY", **state_overrides):
    state = {
        "origem": "mercado_financeiro",
        "intentGroup": intent_group,
        "intentSubgroup": intent_subgroup,
        "symbol": "BTC/USDT",
        "side": "BUY",
        "currentPrice": 50000.0,
        "proposedStopLoss": 49500.0,
        "delta_stop_bps": 100.0,
        "signalSource": "BOOK_IMBALANCE",
        "microstructure": {"spreadBps": 2.0, "depthImbalanceRatio": 3.2},
        "macro": {"regime": "NEUTRAL", "circuitBreakerActive": False},
        "risk": {"accountEquity": 10000, "currentRiskAggregatePct": 0.01, "proposedRiskPct": 0.01},
    }
    state.update(state_overrides)
    return {"state": state, "questions": {"action": {"type": "choice", "criteria": {}}}}


class QuantContractTests(unittest.TestCase):
    def test_pre_entry_preserves_aggressive_verdict(self):
        choice, verdict, rationale, _ = evaluate_quant_rules(payload())
        self.assertEqual(choice, "AUTHORIZE")
        self.assertEqual(verdict, "APPROVE_AGGRESSIVE")
        self.assertEqual(rationale, "V08_IMBALANCE_AGGRESSIVE_APPROVED")

    def test_cooldown_does_not_require_stop_but_requires_evidence(self):
        p = payload(
            "COOLDOWN_AUDIT",
            "LIQUIDITY_SWEEP_REENTRY",
            proposedStopLoss=0,
            delta_stop_bps=0,
            evidence={"liquiditySweepConfirmed": False, "rejectionConfirmed": True},
        )
        choice, _, rationale, _ = evaluate_quant_rules(p)
        self.assertEqual(choice, "VETO")
        self.assertEqual(rationale, "COOLDOWN_MAINTAINED_NO_CONFIRMED_EVIDENCE")

        p["state"]["evidence"]["liquiditySweepConfirmed"] = True
        choice, verdict, _, _ = evaluate_quant_rules(p)
        self.assertEqual(choice, "OVERRIDE_COOLDOWN")
        self.assertEqual(verdict, "OVERRIDE_COOLDOWN")

    def test_lifecycle_uses_structured_evidence_without_stop(self):
        p = payload(
            "POSITION_LIFECYCLE",
            "DEFENSE_CONTRARIAN_FLOW",
            proposedStopLoss=0,
            delta_stop_bps=0,
            currentR=-0.5,
            evidence={"contrarianFlowConfirmed": True},
        )
        choice, _, _, _ = evaluate_quant_rules(p)
        self.assertEqual(choice, "CLOSE_NOW")

        p = payload(
            "POSITION_LIFECYCLE",
            "RUNNER_EVALUATION",
            proposedStopLoss=0,
            delta_stop_bps=0,
            currentR=1.5,
            evidence={"exhaustionConfirmed": False},
        )
        choice, _, _, _ = evaluate_quant_rules(p)
        self.assertEqual(choice, "HOLD")

    def test_nested_quant_schema_rejects_invalid_types_and_side(self):
        with self.assertRaises(ValidationError):
            SystemOneRequest(state={"origem": "mercado_financeiro", "currentPrice": "bad", "side": "BUY"}, questions={"action": {}})
        with self.assertRaises(ValidationError):
            SystemOneRequest(state={"origem": "mercado_financeiro", "currentPrice": 100, "side": "SIDEWAYS"}, questions={"action": {}})


if __name__ == "__main__":
    unittest.main()
