<div align="center">

# Interview System

AI-Powered Interview Platform for Education Assessment

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![React 19](https://img.shields.io/badge/react-19.2-61dafb.svg)](https://react.dev/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

[Quick Start](#quick-start) • [Features](#features) • [API](#api-endpoints) • [Config](#configuration)

**English** | [中文](README_zh.md)

</div>

---

## Features

**Core**
- Multi-LLM support (DeepSeek, OpenAI, Qwen, GLM, ERNIE)
- Dynamic follow-up questions (max 3)
- Context-aware AI responses
- Multi-user concurrent sessions
- Admin dashboard with analytics & export (CSV/JSON/XLSX)
- Public URL sharing with QR code (cloudflared/ngrok)

**UI (React 19 + TypeScript)**
- ShadcnUI + Tailwind CSS
- Dark mode & Command Palette (Ctrl+K)
- PWA support (offline-ready)
- Performance monitoring (Web Vitals)

---

## Quick Start

**Prerequisites:** Python 3.11+ • Node.js 18+

```bash
git clone https://github.com/username/interview_system.git
cd interview_system
python start.py
```

**First Run:** Configure provider (deepseek/openai/qwen/glm/ernie), API key, and optional model override.

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs
- Admin: http://localhost:5173/#admin/overview

**Admin Token:** Auto-generated 32-char password displayed on startup.

**Public Access:**
```bash
python start.py --public  # Requires cloudflared or ngrok
```

<details>
<summary>Manual Setup</summary>

```bash
# Backend
pip install -e ".[api]"
uvicorn interview_system.api.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```
</details>

---

## Architecture

```
interview_system/
├── src/interview_system/
│   ├── api/              # FastAPI (routes, schemas)
│   ├── application/      # Use cases
│   ├── domain/           # Entities, services
│   ├── infrastructure/   # DB, cache, external
│   ├── config/           # Settings, logging
│   └── integrations/     # LLM providers
└── frontend/
    └── src/
        ├── components/   # UI (chat, layout, common)
        ├── stores/       # Zustand state
        ├── hooks/        # TanStack Query
        └── services/     # API client
```

**Stack:** React 19 • TypeScript • Vite • ShadcnUI • Tailwind • FastAPI • SQLite

---

## API Endpoints

**Session Management**
```
POST   /api/session/start              Create session
GET    /api/session/{id}               Get session
POST   /api/session/{id}/message       Send message
POST   /api/session/{id}/undo          Undo exchange
POST   /api/session/{id}/skip          Skip question
POST   /api/session/{id}/restart       Reset session
DELETE /api/session/{id}               Delete session
```

**Admin** (Protected by `X-Admin-Token` header)
```
GET /api/admin/overview                Metrics + time series
GET /api/admin/sessions                Session list (filters + pagination)
GET /api/admin/search                  Search conversation logs
GET /api/admin/export                  Export CSV/JSON/XLSX
```

---

## Configuration

**Backend (.env)**
```ini
API_PROVIDER=deepseek          # deepseek/openai/qwen/zhipu/baidu
API_KEY=your_api_key
API_MODEL=deepseek-chat
API_SECRET_KEY=                # baidu only
DATABASE_URL=sqlite+aiosqlite:///./interview_data.db
ADMIN_TOKEN=                   # Auto-generated on startup
```

**Frontend (.env)**
```ini
VITE_API_URL=http://localhost:8000/api
```

**Providers**

| Provider | Model | API |
|----------|-------|-----|
| DeepSeek | `deepseek-chat` | [platform.deepseek.com](https://platform.deepseek.com/) |
| OpenAI | `gpt-3.5-turbo` | [platform.openai.com](https://platform.openai.com/) |
| Qwen | `qwen-turbo` | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com/) |
| GLM | `glm-4-flash` | [open.bigmodel.cn](https://open.bigmodel.cn/) |
| ERNIE | `ernie-3.5-8k` | [qianfan.baidubce.com](https://qianfan.baidubce.com/) |

**Keywords:** Customize depth-scoring in `config/interview_keywords.yaml`

---

## Troubleshooting

**Input Disabled:** Click "快速访谈" and wait for first question.

**API Validation Failed:** Check `.env` credentials or set `API_KEY=""` for preset-only mode.

---

## Development

```bash
# Tests
cd frontend && npm test
pytest -q

# Build
cd frontend && npm run build
```

---

## License

MIT
