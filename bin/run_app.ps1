# PowerShell — Windows launcher
Write-Host "Starting FastAPI on :8000 and Streamlit on :8501..."
Start-Process -NoNewWindow -FilePath "uvicorn" -ArgumentList "api.main:app", "--reload", "--port", "8000"
streamlit run ui/app.py --server.port 8501
