<div align="center">

# Interview System

**AI-Powered Interview Platform for Holistic Education Assessment**

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
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
- PWA support (offline-ready)
- Performance monitoring (Web Vitals)

</td>
</tr>
</table>

---

## Quick Start

### Prerequisites

- **Python**: 3.11+
- **Node.js**: 18+

### One-Click Launch

```bash
git clone https://github.com/username/interview_system.git
cd interview_system
python start.py
```

Auto-detects environment, installs dependencies, starts all services.

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Admin Dashboard: http://localhost:5173/#admin/overview (requires `ADMIN_TOKEN`)

Press `Ctrl+C` to stop all services.

### Public Access (Tunnel)

```bash
python start.py --public
```

Exposes services via cloudflared/ngrok for remote access.

**Requirements:**
- [Cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/) (recommended, no signup)
- [Ngrok](https://ngrok.com/download) (fallback)

**Output:**
```
前端 公网: https://abc123.trycloudflare.com
后端 公网: https://def456.trycloudflare.com
```

<details>
<summary>Manual Setup</summary>

```bash
# Backend
pip install -e ".[api]"
uvicorn interview_system.api.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend && npm install && npm run dev
```

</details>

---

## Architecture

```
interview_system/
├── src/interview_system/
│   ├── api/                  # FastAPI REST API
│   │   ├── main.py           # App entry
│   │   ├── routes/           # Endpoints
│   │   └── schemas/          # Pydantic models
│   ├── application/          # Application layer (use cases)
│   ├── domain/               # Domain layer (entities/services)
│   ├── infrastructure/       # Infrastructure (DB/cache/external)
│   ├── config/               # Settings + logging
│   ├── core/                 # Data/fixtures (e.g. questions)
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
| vite-plugin-pwa | 1.2 | PWA support |
| workbox-window | 7.4 | Service Worker |
| web-vitals | 5.1 | Performance metrics |

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime |
| FastAPI | 0.110+ | REST API |
| SQLite | - | Database |
| Pydantic | 2.0+ | Validation |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/session/start` | Create session |
| GET | `/api/session/{id}` | Get session |
| GET | `/api/session/{id}/messages` | Get messages |
| POST | `/api/session/{id}/message` | Send message |
| POST | `/api/session/{id}/undo` | Undo exchange |
| POST | `/api/session/{id}/skip` | Skip question |
| POST | `/api/session/{id}/restart` | Reset session |
| GET | `/api/session/{id}/stats` | Get statistics |
| DELETE | `/api/session/{id}` | Delete session |

### Admin (Supervision Dashboard)

Protected by `ADMIN_TOKEN` (request header `X-Admin-Token`). If `ADMIN_TOKEN` is empty, admin endpoints return `404`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/overview` | Metrics + time series |
| GET | `/api/admin/sessions` | Session list (filters + pagination) |
| GET | `/api/admin/search` | Search conversation logs |
| GET | `/api/admin/export` | Export CSV/JSON/XLSX |

---

## Configuration

### Environment Variables

```ini
# Backend (.env)
API_PROVIDER=deepseek
API_KEY=your_api_key_here
API_MODEL=deepseek-chat
DATABASE_URL=sqlite+aiosqlite:///./interview_data.db
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:5173
ADMIN_TOKEN=change_me  # enables /api/admin/*

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

```bash
# Tests
cd frontend && npm test    # Frontend
pytest -q                  # Backend

# Build
cd frontend && npm run build
```

---

## License

MIT
