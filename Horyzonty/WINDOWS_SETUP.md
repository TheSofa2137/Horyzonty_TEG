# Windows Setup Guide — Horyzonty

Follow these steps to run the project on a Windows machine.

---

## Prerequisites

| Tool | Where to get it | Notes |
|------|-----------------|-------|
| **Python 3.11+** | https://www.python.org/downloads/ | Tick *"Add Python to PATH"* during install |
| **Ollama** | https://ollama.com/download | Runs LLaMA 3.2 locally |
| **Neo4j Desktop** | https://neo4j.com/download/ | Graph database |
| **Microsoft C++ Build Tools** | https://visualstudio.microsoft.com/visual-cpp-build-tools/ | *Required only if `chromadb` fails to install — select "Desktop development with C++"* |

---

## 1. Clone / copy the project

```
git clone <repo-url>   # or copy the folder to your machine
cd Horyzonty
```

## 2. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

## 3. Install dependencies

```powershell
pip install -r requirements.txt
```

> **ChromaDB build error?**  Install **Microsoft C++ Build Tools** (link in the table above), restart your terminal, then re-run the pip command.

## 4. Pull the Ollama models

```powershell
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

Ollama must be **running** (check the system tray icon) before starting the backend.

## 5. Set up Neo4j

1. Open Neo4j Desktop and create a new **local DBMS**.
2. Set the password to `12345678` (or update `NEO4J_PW` in `tools.py`, `orchestrator.py`, `flights.py`, `booking_sync.py`).
3. Start the database.

## 6. Configure environment variables (optional)

```powershell
copy env.example .env
```

Edit `.env` and add your Duffel / OpenWeatherMap keys if you have them.  
The app works without them — it will fall back to Neo4j data and mock weather.

## 7. Rebuild the ChromaDB vector store (required on first run)

The `backend/chroma_db` folder was created on macOS and its index files are not portable.  
**Delete it and rebuild locally:**

```powershell
rmdir /s /q backend\chroma_db
python ingest_to_rag.py
```

## 8. Seed the Neo4j database (first run only)

```powershell
python seed_database.py
```

## 9. Start the backend

```powershell
python api.py
```

You should see:

```
Starting FastAPI server on port 8000...
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## 10. Open the frontend

Open `index.html` in your browser directly, or use the VS Code **Live Server** extension (port 5500):

```
http://127.0.0.1:5500/index.html
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `UnicodeEncodeError` with emojis | Set `PYTHONUTF8=1` in your environment, or use **Windows Terminal** instead of the old `cmd.exe` |
| ChromaDB loads 0 chunks / errors mentioning macOS paths | Delete `backend\chroma_db` and run `python ingest_to_rag.py` to rebuild it locally |
| `RuntimeError: no running event loop` / WebSocket errors | Make sure you are on Python 3.11+ and running `python api.py` (the asyncio fix is already in place) |
| `chromadb` install fails with C++ error | Install **Microsoft C++ Build Tools** and re-run `pip install chromadb` |
| Neo4j connection refused | Start the database in Neo4j Desktop first |
| Ollama model not found | Run `ollama pull llama3.2:3b` and `ollama pull nomic-embed-text` |
| Port 8000 already in use | Change `port=8000` in the last line of `api.py` |
