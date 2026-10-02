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

## Railway private-service authentication
- The public Railway target port runs the unchanged upstream `laya-serve` process and continues to require `LAYA_API_KEY`.
- Port `8001` is reserved for a Railway private-network proxy. It is not assigned a public domain.
- The private proxy injects the local bearer and forwards only `/health`, `/v1/systemone`, and `/v1/systemone/batch` to the upstream server on localhost.
- If Railway does not materialize the sealed `LAYA_API_KEY` into a fresh deployment, the supervisor generates a cryptographically strong ephemeral bearer at boot and gives it only to the upstream process and private proxy. Public inference therefore remains bearer-protected even without distributing a shared secret to domain services.
- Domain services should call `http://nexus-decisor-laya-next.railway.internal:8001` and must never embed the Laya secret.
- This proxy is infrastructure glue only; it does not alter prompts, choices, scoring, confidence, routing, or any domain decision.
