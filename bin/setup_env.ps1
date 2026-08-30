# PowerShell — Windows setup
Write-Host "Setting up RAG pipeline environment..."
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install fastapi uvicorn[standard] streamlit openai chromadb pydantic pydantic-settings python-dotenv requests pandas httpx
Write-Host "Done. Add your OPENAI_API_KEY to .env then run bin\run_app.ps1"
