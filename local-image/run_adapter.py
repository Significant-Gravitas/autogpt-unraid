#!/usr/bin/env python3
"""Validate the public local profile, then replace this process with the adapter."""

from __future__ import annotations

import ipaddress
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit


ORIGIN_VARIABLES = ("CHAT_UPSTREAM", "EMBED_UPSTREAM")
MODEL_VARIABLES = (
    "CHAT_FAST_STANDARD_MODEL",
    "GRAPHITI_LLM_MODEL",
    "GRAPHITI_RERANKER_MODEL",
)
INTERNAL_VARIABLES = {
    "CHAT_USE_LOCAL": "true",
    "CHAT_BASE_URL": "http://127.0.0.1:8098/v1",
    "CHAT_API_KEY": "local",
    "GRAPHITI_LLM_BASE_URL": "http://127.0.0.1:8098/v1",
    "GRAPHITI_LLM_API_KEY": "local",
    "GRAPHITI_EMBEDDER_BASE_URL": "http://127.0.0.1:8098/raw/v1",
    "GRAPHITI_EMBEDDER_API_KEY": "local",
    "GRAPHITI_EMBEDDER_MODEL": "nomic-embed-text",
    "STORE_EMBEDDING_MODEL": "nomic-embed-text",
}


def validation_errors(environ: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for name in ORIGIN_VARIABLES:
        value = environ.get(name, "").strip()
        if not value:
            errors.append(f"{name} is required")
            continue
        parsed = urlsplit(value)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            errors.append(
                f"{name} must be an HTTP(S) origin without /v1, credentials, "
                "query, or fragment"
            )
            continue
        hostname = parsed.hostname.lower()
        is_loopback = hostname == "localhost"
        try:
            is_loopback = is_loopback or ipaddress.ip_address(hostname).is_loopback
        except ValueError:
            pass
        if is_loopback:
            errors.append(
                f"{name} cannot use localhost or a loopback address; use "
                "host.docker.internal or a LAN/VPN address"
            )

    for name in MODEL_VARIABLES:
        if not environ.get(name, "").strip():
            errors.append(f"{name} is required")
    for name, expected in INTERNAL_VARIABLES.items():
        if environ.get(name) != expected:
            errors.append(
                f"{name} is managed by the Fully Local image and must not be overridden"
            )
    return errors


def main() -> int:
    errors = validation_errors(dict(os.environ))
    if errors:
        for error in errors:
            print(f"local-model configuration error: {error}", file=sys.stderr)
        return 78

    proxy = Path(__file__).with_name("proxy.py")
    os.execv(sys.executable, [sys.executable, "-u", str(proxy)])
    raise AssertionError("execv returned unexpectedly")


if __name__ == "__main__":
    raise SystemExit(main())
