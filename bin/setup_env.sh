#!/bin/bash
set -e
echo "Setting up RAG pipeline environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn[standard] streamlit openai chromadb pydantic pydantic-settings python-dotenv requests pandas httpx
echo "Done. Activate with: source .venv/bin/activate"
echo "Then add your OPENAI_API_KEY to .env"
