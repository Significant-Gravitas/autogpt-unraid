#!/usr/bin/env python3
"""Docker healthcheck for both configured llama.cpp upstreams."""

import json
import os
import sys
import urllib.request


def check_health(name: str, base_url: str) -> None:
    url = base_url.rstrip("/") + "/health"
    with urllib.request.urlopen(url, timeout=5) as response:
        if response.status != 200:
            raise RuntimeError(f"{name} returned HTTP {response.status}")
        payload = json.loads(response.read())
    if payload.get("status") != "ok":
        raise RuntimeError(f"{name} returned an unexpected health payload")


def main() -> int:
    listen_port = int(os.getenv("LISTEN_PORT", "8098"))
    upstreams = {
        "router": f"http://127.0.0.1:{listen_port}",
        "chat": os.getenv("CHAT_UPSTREAM", "http://127.0.0.1:8099"),
        "embeddings": os.getenv("EMBED_UPSTREAM", "http://127.0.0.1:8100"),
    }
    for name, base_url in upstreams.items():
        try:
            check_health(name, base_url)
        except Exception:
            # urllib exceptions include the full configured URL. Keep health
            # output useful without leaking an upstream origin or response.
            print(f"unhealthy: {name} endpoint is not ready", file=sys.stderr)
            return 1
    print("healthy: router, chat, and embeddings upstreams are ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
