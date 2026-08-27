#!/usr/bin/env bash
set -Eeuo pipefail

/usr/local/bin/autogpt-healthcheck
exec /app/autogpt_platform/backend/.venv/bin/python /opt/autogpt-local/healthcheck.py
