<div align="center">

# Interview System

**AI-Powered Interview Platform for Holistic Education Assessment**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-19.2-61dafb.svg)](https://react.dev/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()

[Quick Start](#quick-start) | [Features](#features) | [Architecture](#architecture) | [Configuration](#configuration)

**English** | [中文](README_zh.md)

</div>

---

## Features

<table>
<tr>
<td width="50%">

**Core Capabilities**
- Multi-LLM support (DeepSeek, OpenAI, Qwen, GLM, ERNIE)
- Dynamic follow-up questions (max 3 per question)
- Context-aware AI responses
- Multi-user concurrent sessions

</td>
<td width="50%">

**v3.0 Modern UI**
- React 19 + TypeScript + ShadcnUI
- Bento Grid layout
- Dark mode support
- Command Palette (Ctrl+K)
- Glassmorphism effects
- Micro-interactions

</td>
</tr>
</table>

---

## Quick Start

### Prerequisites

- **Python**: 3.10+
- **Node.js**: 18+ (for frontend)
- **OS**: Windows 10/11, macOS, Linux

### Backend Setup

```bash
# Clone repository
git clone https://github.com/username/interview_system.git
cd interview_system

# Create virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/macOS

# Install backend
pip install -e ".[api]"

# Start API server
uvicorn interview_system.api.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

---

## Architecture

```
interview_system/
├── src/interview_system/
│   ├── api/                  # FastAPI REST API
│   │   ├── main.py           # App entry
│   │   ├── routes/           # Endpoints
│   │   └── schemas/          # Pydantic models
│   ├── core/                 # Business logic
│   ├── services/             # Session management
│   ├── data/                 # Database layer
│   └── integrations/         # LLM providers
├── frontend/                 # React SPA
│   ├── src/
│   │   ├── components/       # UI components
│   │   │   ├── chat/         # Chatbot, MessageBubble
│   │   │   ├── layout/       # Layout, Header, Sidebar
│   │   │   └── common/       # ThemeProvider, CommandPalette
│   │   ├── stores/           # Zustand state
│   │   ├── hooks/            # TanStack Query hooks
│   │   ├── services/         # API client
│   │   └── types/            # TypeScript types
│   └── package.json
└── llmdoc/                   # LLM documentation
```

---

## Tech Stack

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.2 | UI framework |
| TypeScript | 5.9 | Type safety |
| Vite | 7.3 | Build tool |
| ShadcnUI | latest | Component library |
| Tailwind CSS | 3.4 | Styling |
| Zustand | 5.0 | State management |
| TanStack Query | 5.90 | Data fetching |

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.10+ | Runtime |
| FastAPI | 0.110+ | REST API |
| SQLite | - | Database |
| Pydantic | 2.0+ | Validation |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/session/start` | Create session |
| GET | `/api/session/{id}` | Get session |
| POST | `/api/session/{id}/message` | Send message |
| POST | `/api/session/{id}/undo` | Undo exchange |
| POST | `/api/session/{id}/skip` | Skip question |
| POST | `/api/session/{id}/restart` | Reset session |
| GET | `/api/session/{id}/stats` | Get statistics |

---

## Configuration

### Environment Variables

```ini
# Backend (.env)
API_PROVIDER=deepseek
API_KEY=your_api_key_here
API_MODEL=deepseek-chat

# Frontend (.env)
VITE_API_URL=http://localhost:8000/api
```

### API Providers

| Provider | Model | Website |
|----------|-------|---------|
| DeepSeek | `deepseek-chat` | [platform.deepseek.com](https://platform.deepseek.com/) |
| OpenAI | `gpt-3.5-turbo` | [platform.openai.com](https://platform.openai.com/) |
| Qwen | `qwen-turbo` | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com/) |
| GLM | `glm-4-flash` | [open.bigmodel.cn](https://open.bigmodel.cn/) |
| ERNIE | `ernie-3.5-8k` | [qianfan.baidubce.com](https://qianfan.baidubce.com/) |

---

## Development

### Run Tests

```bash
# Frontend tests
cd frontend && npm test

# Backend tests
pytest -q
```

### Build Production

```bash
# Frontend
cd frontend && npm run build

# Output: frontend/dist/
```

---

## Design System

### Colors

| Token | Light | Dark |
|-------|-------|------|
| Background | `#F5F7FA` | `#0F172A` |
| Card | `#FFFFFF` | `#1E293B` |
| Primary | `#7C3AED` | `#7C3AED` |
| Muted | `#64748B` | `#94A3B8` |

### Spacing

8px grid system: `4px`, `8px`, `16px`, `24px`, `32px`

### Effects

- Card shadow: `0 1px 3px rgba(0,0,0,0.05)`
- Glassmorphism: `backdrop-filter: blur(10px)`
- Hover lift: `transform: translateY(-2px)`

---

## License

MIT License

---

## Contributing

Contributions welcome.
