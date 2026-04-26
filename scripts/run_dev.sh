#!/usr/bin/env bash
# Start backend + frontend in dev mode.
set -e

uvicorn backend.main:app --reload --port 8000 &
BACK_PID=$!
trap "kill $BACK_PID" EXIT

streamlit run frontend/app.py
