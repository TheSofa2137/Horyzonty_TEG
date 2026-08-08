# Frontend README

Complete React TypeScript frontend for the Horyzonty AI Trip Planner.

## 🚀 Quick Start

### Start the App (Pick One Method)

**Method 1: Full Stack (Easiest)**
```bash
cd ..
./start.sh
```
Starts both backend and frontend. Opens http://localhost:3000

**Method 2: Separate Terminals**
```bash
cd ..
./start-backend.sh      # Terminal 1
./start-frontend.sh     # Terminal 2
```

**Method 3: Manual**
```bash
npm start               # Dev server on port 3000
```

## ✨ Features

- 💬 **Real-time chat** - Messages stream as they're received
- 📚 **Source citations** - Shows retrieved documents under responses
- 🔗 **WebSocket integration** - Bidirectional communication with backend
- 🌍 **Responsive design** - Works on desktop, tablet, mobile
- 🎨 **Beautiful UI** - Purple gradient theme with smooth animations
- ⚡ **Hot reload** - Changes instantly in development
- 🧪 **Mock backend** - Complete test server included
- 🔒 **TypeScript strict** - Full type safety

## 📁 Project Structure

```
src/
├── App.tsx                          Main app component
├── App.css                          Main layout & styles
├── index.tsx                        React entry point
├── index.css                        Global styles
├── components/
│   ├── ChatInterface.tsx            Chat UI (250+ lines)
│   ├── ChatInterface.css            Chat styling (280+ lines)
│   ├── SourcePanel.tsx              Source panel
│   └── SourcePanel.css              Source styling
└── hooks/
    ├── useWebSocket.ts              WebSocket management
    └── useTripState.ts              State management
```

## 🔌 Backend Integration

### Expected API Format

**Frontend sends:**
```json
{
  "message": "Plan 4 days in Lisbon"
}
```

**Backend responds:**
```json
{
  "type": "response",
  "content": "Here's your itinerary...",
  "sources": ["Source 1", "Source 2"]
}
```

### Configuration

Edit `.env`:
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
```

## 🎨 Customization

### Change Colors

Edit `App.css`:
```css
/* Current: purple gradient */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Try: blue gradient */
background: linear-gradient(135deg, #667eea 0%, #1e90ff 100%);
```

### Change Text

Edit `components/ChatInterface.tsx` for placeholder text and prompts.

## 📦 Technology Stack

- React 18.2.0
- TypeScript 4.9.5 (strict mode)
- CSS3
- WebSocket API
- 1303 npm packages

## 🚀 Commands

```bash
npm start              # Dev server
npm run build         # Production build
npm test              # Run tests
../verify-frontend.sh # Check setup
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 3000 in use | `lsof -ti:3000 \| xargs kill -9` |
| Connection refused | Backend must run on port 8000 |
| Blank page | Check browser console (F12) |
| Styles not loading | Clear cache (Ctrl+Shift+Delete) |

## 💡 Example Prompts

```
"Plan 4 days in Lisbon for food lovers, €100/day"
"Find flights from Warsaw to Barcelona"
"What museums are best in Rome?"
"Replace Day 2 lunch with something cheaper"
```

## 📱 Browser Support

Chrome 90+, Firefox 88+, Safari 14+, Edge 90+, Mobile browsers

## 🌐 Deploy

```bash
npm run build
# Deploy the 'build/' folder to Vercel, Netlify, AWS, etc.
```

---

**Version**: 1.0.0 | **Status**: Production Ready ✅


