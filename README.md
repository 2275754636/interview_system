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
- Admin dashboard with analytics & export (CSV/JSON/XLSX)
- Public URL sharing with QR code (cloudflared/ngrok)
- External configuration (YAML-based keywords)

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

#### First-Run Configuration

On first run, you'll be prompted to:
- Select a provider (deepseek/openai/qwen/glm/ernie)
- Enter API Key (masked)
- Enter Secret Key for ERNIE (masked)
- Optionally override the model (press Enter to use default)

**API Validation:**
- The system validates your API key before starting
- If validation fails, the system automatically falls back to preset questions
- You can still use the interview system without a valid API key (limited to preset questions)

**Admin Token:**
- System automatically generates a 32-character random password on startup
- Token is displayed prominently in the terminal (after startup completes)
- New token generated on each startup for enhanced security

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Admin Dashboard: http://localhost:5173/#admin/overview

Press `Ctrl+C` to stop all services.

### Public Access (Tunnel)

```bash
python start.py --public
```

Exposes services via cloudflared/ngrok for remote access.

**Requirements:**
- [Cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/) (recommended, no signup)
- [Ngrok](https://ngrok.com/download) (fallback)

**Features:**
- Prints public URLs when tunnel is ready
- Displays ASCII QR code in terminal for easy mobile access
- Frontend shows QR code dialog (click share icon in header)
- Tunnel state persisted in `.public_url_state.json`

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
API_PROVIDER=deepseek  # deepseek/openai/qwen/zhipu/baidu
API_KEY=your_api_key_here
API_MODEL=deepseek-chat
API_SECRET_KEY=your_secret_key_here  # baidu only
DATABASE_URL=sqlite+aiosqlite:///./interview_data.db
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:5173
ADMIN_TOKEN=auto_generated  # Auto-generated on startup, no manual config needed

# Frontend (.env)
VITE_API_URL=http://localhost:8000/api
```

**Notes:**
- `glm` is stored as `API_PROVIDER=zhipu` in `.env`
- `ernie` is stored as `API_PROVIDER=baidu` in `.env`
- Setting `API_KEY=""` (empty) forces preset questions only (no AI followups)
- `ADMIN_TOKEN` is auto-generated on each startup, no manual configuration required

### API Providers

| Provider | Model | Website |
|----------|-------|---------|
| DeepSeek | `deepseek-chat` | [platform.deepseek.com](https://platform.deepseek.com/) |
| OpenAI | `gpt-3.5-turbo` | [platform.openai.com](https://platform.openai.com/) |
| Qwen | `qwen-turbo` | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com/) |
| GLM | `glm-4-flash` | [open.bigmodel.cn](https://open.bigmodel.cn/) |
| ERNIE | `ernie-3.5-8k` | [qianfan.baidubce.com](https://qianfan.baidubce.com/) |

### Interview Keywords Configuration

Depth-scoring keywords are externalized to `config/interview_keywords.yaml`:

```yaml
depth_keywords:
  - "具体"
  - "例如"
  - "因为"
  # ... more keywords
```

The system automatically loads this file with fallback to hardcoded defaults. You can customize keywords without modifying code.

---

## Troubleshooting

### Text Input Disabled

**Symptom:** Cannot type in the message input field.

**Cause:** Session not started, or waiting for the first question.

**Solution:**
- Click "快速访谈" (Quick Interview) and wait until the first question appears.

### API Validation Failed

**Symptom:** Warning message during startup:
```
⚠ API 验证失败: [error details]
  回退模式: 使用预设问题
```

**Cause:** Invalid API key, network issues, or provider service unavailable.

**Solution:**
- Check `.env` (`API_PROVIDER`, `API_KEY`, `API_SECRET_KEY` for baidu)
- Re-run `python start.py` to reconfigure
- Or force preset mode with `API_KEY=""`

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
