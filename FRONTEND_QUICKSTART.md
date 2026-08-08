// ...existing code... # Getting Started

Quick guide to run the Horyzonty Trip Planner frontend.

## 🚀 Quick Start

**One Command:**
```bash
./start.sh
```

Opens browser to http://localhost:3000

**Separate Terminals:**
```bash
./start-backend.sh      # Terminal 1
./start-frontend.sh     # Terminal 2
```

**Manual:**
```bash
cd frontend
npm start               # Terminal 1
cd backend
./test_websocket.py    # Terminal 2 (requires Python venv)
```

## 📂 Project Structure

```
Horyzonty_TEG/
├── frontend/                    React app (start here)
│   ├── src/                     React components & hooks
│   ├── package.json             Dependencies (1303 packages)
│   ├── .env                     Backend URLs
│   └── README.md                Frontend documentation
│
├── backend/
│   ├── main.py                  Your FastAPI app
│   ├── test_websocket.py        Mock server for testing
│   └── ... (other files)
│
├── scripts/
│   ├── ingest.py
│   ├── populate_graph.py
│   └── test_rag.py
│
├── data/
│   └── raw/
│       └── lisbon.md
│
├── start.sh                     Full stack startup
├── start-frontend.sh            Frontend only
├── start-backend.sh             Backend + test server
└── verify-frontend.sh           Setup verification
```

## ✨ What's Included

### React Frontend
- 3 components (App, ChatInterface, SourcePanel)
- 2 custom hooks (useWebSocket, useTripState)
- Real-time WebSocket chat
- Beautiful gradient UI
- Fully responsive
- TypeScript strict mode

### Backend Integration
- Mock server (test_websocket.py) for testing
- WebSocket communication
- Auto-reconnect logic
- Type-safe messages

### Scripts
- `./start.sh` - Full stack (both services)
- `./start-frontend.sh` - Frontend only
- `./start-backend.sh` - Backend with mock server
- `./verify-frontend.sh` - Setup verification

## 🎯 Example Usage

Once running at http://localhost:3000:

```
"Plan 4 days in Lisbon for food lovers, budget €100/day"
"Find flights from Warsaw to Barcelona in June"
"What museums are best in Rome for first-time visitors?"
"Replace Day 2 lunch with something cheaper"
```

## ⚙️ Environment Setup

Frontend configuration in `frontend/.env`:
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
```

Modify if your backend runs on a different port/host.

## 🔌 Backend Integration

The frontend expects your backend to:

1. Accept WebSocket connections at `ws://localhost:8000/ws`
2. Receive messages: `{ "message": "user's question" }`
3. Send responses: `{ "type": "response", "content": "...", "sources": [...] }`

Included mock backend provides exactly this format for testing.

## 📚 Documentation

- **frontend/README.md** - Complete frontend documentation
- **backend/test_websocket.py** - Mock server with examples

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 3000 in use | `lsof -ti:3000 \| xargs kill -9` |
| Connection refused | Backend must run on port 8000 |
| WebSocket error | Check REACT_APP_WS_URL in frontend/.env |
| Blank page | Open browser console (F12) for errors |
| Dependencies issue | `cd frontend && npm install` |

## 📊 Tech Stack

- **Frontend**: React 18, TypeScript, CSS3, WebSocket
- **Backend**: FastAPI, Python
- **Mock Server**: test_websocket.py (complete with sample data)
- **Total Packages**: 1303 npm + Python dependencies

## ✅ Verification

Run setup check:
```bash
./verify-frontend.sh
```

Shows installation status, dependencies, and file presence.

## 🚀 Next Steps

1. **Run**: `./start.sh`
2. **Test**: Try example prompts
3. **Customize**: Edit colors in `frontend/src/App.css`
4. **Integrate**: Connect your backend (replace test_websocket.py)
5. **Deploy**: `cd frontend && npm run build`

## 💡 Tips

- Use `./start.sh` for quick testing
- Use separate terminals for debugging
- Check `frontend/README.md` for detailed frontend docs
- Run `./verify-frontend.sh` if setup issues arise
- Mock server is perfect for UI development

---

**Ready to go!** Run `./start.sh` and open http://localhost:3000
