# Nexus integration boundary

This branch is pinned to upstream Laya v0.3.23 (commit d8a2e59781ca135169a36095056132e273cd9938).

## Allowed responsibilities
- Serve the upstream Jev-compatible `/v1/systemone` contract.
- Return typed `choice`, `score`, and `noul` decisions with calibrated answer confidence.
- Authentication, health, model loading, routing, and inference observability.

## Forbidden responsibilities
- Trading strategy rules or market-specific thresholds.
- Solana/RugCheck/Jupiter logic.
- Mercado Financeiro spread, stop, position lifecycle, sizing, or execution rules.
- Wallet, order, swap, or broker execution.
- Persistence of domain positions or financial state.

Domain applications must validate deterministic invariants before consulting Laya and must own all execution.
Changes to this branch should remain upstream-aligned; Railway-specific integration must be minimal and explicit.
