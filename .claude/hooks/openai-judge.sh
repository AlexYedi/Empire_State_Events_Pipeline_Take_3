#!/usr/bin/env bash
# openai-judge.sh — the OpenAI seat (YED-209). Thin shim so the seat is invoked like gemini-judge.sh; all logic
# lives in openai_judge.py (Python keeps the API key out of argv, where `ps` could read it).
exec python3 "$(dirname "$0")/openai_judge.py" "$@"
