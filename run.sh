#!/usr/bin/env bash
cd "$(dirname "$0")"
PYTHONPATH=.deps exec python3 -m uvicorn app:app --host 127.0.0.1 --port "${PORT:-8000}" "$@"
