<div align="center">

# 访谈系统

AI驱动的教育评估访谈平台

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![React 19](https://img.shields.io/badge/react-19.2-61dafb.svg)](https://react.dev/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

[快速开始](#快速开始) • [功能特性](#功能特性) • [API](#api端点) • [配置](#配置说明)

[English](README.md) | **中文**

</div>

---

## 功能特性

**核心能力**
- 多LLM支持 (DeepSeek、OpenAI、通义千问、智谱GLM、文心一言)
- 动态追问 (每题最多3次)
- 上下文感知AI响应
- 多用户并发会话
- 后台监管仪表盘，支持数据分析与导出 (CSV/JSON/XLSX)
- 公网URL分享，支持二维码扫描 (cloudflared/ngrok)

**现代化UI (React 19 + TypeScript)**
- ShadcnUI + Tailwind CSS
- 深色模式 & 命令面板 (Ctrl+K)
- PWA支持 (离线可用)
- 性能监控 (Web Vitals)

---

## 快速开始

**环境要求:** Python 3.11+ • Node.js 18+

```bash
git clone https://github.com/username/interview_system.git
cd interview_system
python start.py
```

**首次运行:** 配置提供商 (deepseek/openai/qwen/glm/ernie)、API密钥和可选模型覆盖。

**访问地址:**
- 前端: http://localhost:5173
- 后端 API: http://localhost:8000/docs
- 后台监管: http://localhost:5173/#admin/overview

**后台监管 Token:** 启动时自动生成32位随机密码并显示在终端。

**公网访问:**
```bash
python start.py --public  # 需要 cloudflared 或 ngrok
```

<details>
<summary>手动启动</summary>

```bash
# 后端
pip install -e ".[api]"
uvicorn interview_system.api.main:app --reload --port 8000

# 前端
cd frontend && npm install && npm run dev
```
</details>

---

## 架构设计

```
interview_system/
├── src/interview_system/
│   ├── api/              # FastAPI (路由, schemas)
│   ├── application/      # 用例
│   ├── domain/           # 实体, 服务
│   ├── infrastructure/   # DB, 缓存, 外部
│   ├── config/           # 配置, 日志
│   └── integrations/     # LLM集成
└── frontend/
    └── src/
        ├── components/   # UI (chat, layout, common)
        ├── stores/       # Zustand状态
        ├── hooks/        # TanStack Query
        └── services/     # API客户端
```

**技术栈:** React 19 • TypeScript • Vite • ShadcnUI • Tailwind • FastAPI • SQLite

---

## API端点

**会话管理**
```
POST   /api/session/start              创建会话
GET    /api/session/{id}               获取会话
POST   /api/session/{id}/message       发送消息
POST   /api/session/{id}/undo          撤销交换
POST   /api/session/{id}/skip          跳过问题
POST   /api/session/{id}/restart       重置会话
DELETE /api/session/{id}               删除会话
```

**后台监管** (需要 `X-Admin-Token` 请求头)
```
GET /api/admin/overview                指标概览 + 时间序列
GET /api/admin/sessions                会话列表 (过滤 + 分页)
GET /api/admin/search                  搜索对话记录
GET /api/admin/export                  导出 CSV/JSON/XLSX
```

---

## 配置说明

**后端 (.env)**
```ini
API_PROVIDER=deepseek          # deepseek/openai/qwen/zhipu/baidu
API_KEY=your_api_key
API_MODEL=deepseek-chat
API_SECRET_KEY=                # 仅百度需要
DATABASE_URL=sqlite+aiosqlite:///./interview_data.db
ADMIN_TOKEN=                   # 启动时自动生成
```

**前端 (.env)**
```ini
VITE_API_URL=http://localhost:8000/api
```

**服务商**

| 服务商 | 模型 | API |
|--------|------|-----|
| DeepSeek | `deepseek-chat` | [platform.deepseek.com](https://platform.deepseek.com/) |
| OpenAI | `gpt-3.5-turbo` | [platform.openai.com](https://platform.openai.com/) |
| 通义千问 | `qwen-turbo` | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com/) |
| 智谱GLM | `glm-4-flash` | [open.bigmodel.cn](https://open.bigmodel.cn/) |
| 文心一言 | `ernie-3.5-8k` | [qianfan.baidubce.com](https://qianfan.baidubce.com/) |

**关键词配置:** 在 `config/interview_keywords.yaml` 中自定义深度评分关键词

---

## 故障排除

**输入被禁用:** 点击"快速访谈"并等待第一个问题出现。

**API 验证失败:** 检查 `.env` 凭据或设置 `API_KEY=""` 强制使用预设问题模式。

---

## 开发指南

```bash
# 测试
cd frontend && npm test
pytest -q

# 构建
cd frontend && npm run build
```

---

## 许可证

MIT
