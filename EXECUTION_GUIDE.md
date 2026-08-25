# Execution Guide — Capstone RAG Pipeline

## What you're building
End-to-end production RAG system: ingest docs → chunk → embed → vector DB → FastAPI → Streamlit UI → evaluation.

---

## Prerequisites checklist
- [ ] Python 3.11+ installed
- [ ] Ollama running locally (`ollama serve`) — already set up ✅
- [ ] Docker Desktop installed (for containerised deployment)
- [ ] Vocareum OpenAI API key (from portal GenAI section)
- [ ] GitHub account + Git configured

---

## Step 1: Environment setup
```powershell
cd "D:\Saptarshi\claude_ProjectAtlas\07_STUDY\7.2 Courses\AI Engineering_IITMP\Projects\02_capstone_rag_pipeline"

# Copy and fill .env
Copy-Item .env.example .env
notepad .env   # paste your Vocareum API key

# Install Python deps (choose one):
# Option A: pip (standard)
pip install fastapi uvicorn streamlit openai langchain chromadb pydantic pydantic-settings python-dotenv pytest httpx tiktoken

# Option B: uv (faster, modern — if installed)
# pip install uv
# uv sync
```

---

## Step 2: Verify setup
```powershell
# Test OpenAI connection (Vocareum key)
python -c "
from openai import OpenAI; import os; from dotenv import load_dotenv
load_dotenv()
c = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
r = c.chat.completions.create(model='gpt-4o-mini', messages=[{'role':'user','content':'ping'}])
print('OpenAI OK:', r.choices[0].message.content[:50])
"

# Test Ollama (local, free)
python -c "
from openai import OpenAI
c = OpenAI(api_key='ollama', base_url='http://localhost:11434/v1')
r = c.chat.completions.create(model='llama3.2', messages=[{'role':'user','content':'ping'}])
print('Ollama OK:', r.choices[0].message.content[:50])
"
```

To toggle between OpenAI and Ollama, edit `.env`:
```
USE_OLLAMA=false   # → OpenAI (Vocareum key)
USE_OLLAMA=true    # → Ollama local (free, private)
```

---

## Step 3: Add your data
Drop documents into `data/raw_markdown/` (`.md` or `.txt` files).
These become your knowledge base.

Ideas for your dataset:
- Property documents from `03_PROPERTIES/` (anonymised excerpts)
- Financial summaries from Atlas reports
- Or ask Vishnu to share one of the 5–6 use case datasets

---

## Step 4: Milestone 1 — Documents (do first)

### 4a. Capstone Framing Document
Edit `docs/adr/0001-capstone-framing.md`:
```markdown
# ADR 0001: Capstone Framing
## Use case
[What questions will your RAG answer? Whose data?]
## Dataset
[What documents? How many? Source?]
## Tech stack decisions
- LLM: GPT-4O Mini (fast, cheap, good enough for RAG generation)
- Vector DB: ChromaDB (local, zero setup, perfect for this project)
- Embeddings: text-embedding-ada-002 (OpenAI) OR nomic-embed-text (Ollama, free)
## Trade-offs
- ChromaDB vs Pinecone: chose local (no cost, no internet dependency; limitation: not cloud-scalable)
- Mini vs 4O: chose Mini (3× faster, 10× cheaper; limitation: less deep reasoning)
```

### 4b. Stakeholder Map
Edit `docs/stakeholder-map-template.md` with who uses/builds/maintains the system.

### 4c. Initial golden set
Edit `data/golden_set.jsonl` — add at least 5 Q&A pairs:
```jsonl
{"query": "What is the gross yield on property X?", "expected_answer": "5.2%", "context": "Property X rents at $2,600/month. Purchase price $600,000."}
```

---

## Step 5: Run the app locally
```powershell
# Terminal 1 — FastAPI backend
uvicorn api.main:app --reload --port 8000

# Terminal 2 — Streamlit frontend
streamlit run ui/app.py --server.port 8501

# Open browser:
# API docs: http://localhost:8000/docs
# UI:       http://localhost:8501
```

---

## Step 6: Run tests
```powershell
pytest tests/ -v --tb=short
```

---

## Step 7: Docker (containerised deployment)
```powershell
# Build and run both API + UI via Docker Compose
docker-compose up -d --build

# API at http://localhost:8000
# UI  at http://localhost:8501

# Stop
docker-compose down
```

Ensure `.env` is present — docker-compose picks it up via `env_file: .env`.

---

## Step 8: Evaluation against golden set
```powershell
# Run standard evaluation
python scripts/run_eval.py --dataset data/golden_set.jsonl --judge llm_judge

# Run full RAG pipeline evaluation
python scripts/run_rag_eval.py --config config/settings.py

# A/B test two prompts
python scripts/run_pairwise.py --model_a gpt-4o-mini --model_b gpt-4o
```

---

## Step 9: GitHub setup
```powershell
cd "D:\Saptarshi\claude_ProjectAtlas\07_STUDY\7.2 Courses\AI Engineering_IITMP\Projects\02_capstone_rag_pipeline"

git init -b main
git config user.email "alchemist227@gmail.com"
git config user.name "Saptarshi Sengupta"
git add --all -- ':!.env' ':!data/db/*' ':!data/uploads/*'
git commit -m "feat: initial capstone RAG scaffold (generate_rag_structure.py)"

# Create private repo on GitHub: https://github.com/new
# Name suggestion: iitmp-capstone-rag-pipeline
git remote add origin https://github.com/alchemist227/<repo-name>.git
git push -u origin main
```

Ongoing commit pattern:
```powershell
git checkout -b feat/milestone-1-adr
# ... fill in docs/adr/0001-capstone-framing.md ...
git add .
git commit -m "feat(milestone-1): add capstone framing doc and stakeholder map"
git push origin feat/milestone-1-adr
# → open PR on GitHub → merge to main
```

---

## Milestone 1 checklist (Vishnu's DR1 requirements)
- [ ] `docs/adr/0001-capstone-framing.md` complete
- [ ] `docs/stakeholder-map-template.md` complete
- [ ] `api/main.py` — `GET /health` returns 200
- [ ] `ui/app.py` — opens without error
- [ ] `data/golden_set.jsonl` — at least 5 entries
- [ ] GitHub repo created + first commit pushed
- [ ] DR1 session booked with Vishnu

## Capstone rubric reminder
| Level | What's needed |
|-------|--------------|
| Level 1 | Demo works — RAG returns answers |
| Level 2 | Demo + unit tests pass |
| Level 3 | Demo + tests + eval metrics (groundedness, hit rate) |
| Level 4 | All above + ADR complete + trade-offs documented |

---

## Tool reference
| Need | Command |
|------|---------|
| Count tokens before API call | `import tiktoken; enc=tiktoken.encoding_for_model("gpt-4o"); len(enc.encode(text))` |
| Use Ollama for embeddings (free) | Set `USE_OLLAMA=true` + `ollama pull nomic-embed-text` |
| See ChromaDB contents | `python -c "import chromadb; c=chromadb.PersistentClient('data/db/chroma'); print(c.list_collections())"` |
| Reset vector DB | Delete `data/db/chroma/` folder |
| Check Docker containers | `docker ps` |
| View eval results | `python -c "import sqlite3,pandas as pd; print(pd.read_sql('SELECT * FROM runs', sqlite3.connect('data/db/eval_runs.db')))"` |
