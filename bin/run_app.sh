#!/bin/bash
# Run FastAPI backend + Streamlit UI concurrently
set -e
# Activate venv if present
[ -f .venv/bin/activate ] && source .venv/bin/activate
echo "Starting FastAPI on :8000 and Streamlit on :8501..."
uvicorn api.main:app --reload --port 8000 &
BACKEND_PID=$!
streamlit run ui/app.py --server.port 8501
kill $BACKEND_PID 2>/dev/null || true
