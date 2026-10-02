"""Railway-only private proxy for the upstream Laya server.

The upstream laya-serve process remains unchanged and continues to enforce
LAYA_API_KEY on the Railway public port. This companion proxy listens on an
additional private-network port and injects the local bearer before forwarding
requests to the upstream process on localhost.

No domain/business rules live here. The proxy only solves secret distribution
between services in the same isolated Railway environment.
"""

from __future__ import annotations

import asyncio
import http.client
import os
import subprocess
import sys
import threading
from typing import Iterable

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response


PUBLIC_PORT = int(os.environ.get("PORT") or os.environ.get("LAYA_PORT") or "8000")
INTERNAL_PORT = int(os.environ.get("LAYA_INTERNAL_PROXY_PORT") or "8001")
PROXY_TIMEOUT_SECONDS = float(os.environ.get("LAYA_INTERNAL_PROXY_TIMEOUT_SECONDS") or "45")
MAX_BODY_BYTES = 2 * 1024 * 1024
ALLOWED_PATHS = {"/health", "/v1/systemone", "/v1/systemone/batch"}
HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}

app = FastAPI(
    title="Laya Railway Private Proxy",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


def _clean_request_headers(headers: Iterable[tuple[str, str]], api_key: str) -> dict[str, str]:
    """Return safe headers for localhost upstream and inject the local bearer."""
    result: dict[str, str] = {}
    for name, value in headers:
        lower = name.lower()
        if lower in HOP_BY_HOP or lower in {"authorization", "host", "content-length"}:
            continue
        result[name] = value
    result["Authorization"] = f"Bearer {api_key}"
    result["Host"] = f"127.0.0.1:{PUBLIC_PORT}"
    return result


def _forward(method: str, target: str, body: bytes, headers: dict[str, str]) -> tuple[int, list[tuple[str, str]], bytes]:
    conn = http.client.HTTPConnection("127.0.0.1", PUBLIC_PORT, timeout=PROXY_TIMEOUT_SECONDS)
    try:
        conn.request(method, target, body=body if body else None, headers=headers)
        upstream = conn.getresponse()
        response_body = upstream.read()
        response_headers = [
            (name, value)
            for name, value in upstream.getheaders()
            if name.lower() not in HOP_BY_HOP and name.lower() != "content-length"
        ]
        return upstream.status, response_headers, response_body
    finally:
        conn.close()


@app.api_route("/{path:path}", methods=["GET", "POST"])
async def private_proxy(request: Request, path: str):
    target_path = "/" + path
    if target_path not in ALLOWED_PATHS:
        return JSONResponse({"detail": "private route not allowed"}, status_code=404)

    api_key = os.environ.get("LAYA_API_KEY")
    if not api_key:
        return JSONResponse({"detail": "internal auth unavailable"}, status_code=503)

    body = await request.body()
    if len(body) > MAX_BODY_BYTES:
        return JSONResponse({"detail": "request body too large"}, status_code=413)

    query = request.url.query
    target = target_path + (f"?{query}" if query else "")
    headers = _clean_request_headers(list(request.headers.items()), api_key)

    try:
        status, response_headers, response_body = await asyncio.to_thread(
            _forward,
            request.method,
            target,
            body,
            headers,
        )
    except Exception as exc:
        return JSONResponse(
            {"detail": "upstream unavailable", "error_type": type(exc).__name__},
            status_code=503,
        )

    return Response(
        content=response_body,
        status_code=status,
        headers=dict(response_headers),
    )


def main() -> None:
    api_key = os.environ.get("LAYA_API_KEY")
    if not api_key:
        sys.exit("LAYA_API_KEY is required for Railway public/private operation")

    if INTERNAL_PORT == PUBLIC_PORT:
        sys.exit("LAYA_INTERNAL_PROXY_PORT must differ from PORT/LAYA_PORT")

    upstream_env = os.environ.copy()
    upstream_env["LAYA_PORT"] = str(PUBLIC_PORT)

    upstream = subprocess.Popen(["laya-serve"], env=upstream_env)

    config = uvicorn.Config(
        app,
        host="::",
        port=INTERNAL_PORT,
        log_level=os.environ.get("LAYA_INTERNAL_PROXY_LOG_LEVEL", "warning"),
        access_log=False,
    )
    server = uvicorn.Server(config)
    upstream_exit: list[int] = []

    def watch_upstream() -> None:
        code = upstream.wait()
        upstream_exit.append(code)
        server.should_exit = True

    watcher = threading.Thread(target=watch_upstream, name="laya-upstream-watch", daemon=True)
    watcher.start()

    print(
        f"[RailwayPrivateProxy] internal=http://[::]:{INTERNAL_PORT} "
        f"-> upstream=http://127.0.0.1:{PUBLIC_PORT}"
    )

    try:
        server.run()
    finally:
        if upstream.poll() is None:
            upstream.terminate()
            try:
                upstream.wait(timeout=10)
            except subprocess.TimeoutExpired:
                upstream.kill()
                upstream.wait(timeout=5)

    if upstream_exit:
        code = upstream_exit[-1]
        if code != 0:
            raise SystemExit(code)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
