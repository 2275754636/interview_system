<div align="center">

# 访谈系统

**AI驱动的五育并举教育评估访谈平台**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-19.2-61dafb.svg)](https://react.dev/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()

[快速开始](#快速开始) | [功能特性](#功能特性) | [架构设计](#架构设计) | [配置说明](#配置说明)

[English](README.md) | **中文**

</div>

---

## 功能特性

<table>
<tr>
<td width="50%">

**核心能力**
- 多LLM支持 (DeepSeek、OpenAI、通义千问、智谱GLM、文心一言)
- 动态追问 (每题最多3次)
- 上下文感知AI响应
- 多用户并发会话

</td>
<td width="50%">

**v3.0 现代化UI**
- React 19 + TypeScript + ShadcnUI
- Bento Grid 便当盒布局
- 深色模式支持
- 命令面板 (Ctrl+K)
- 玻璃拟态效果
- 微交互动画

</td>
</tr>
</table>

---

## 快速开始

### 环境要求

- **Python**: 3.10+
- **Node.js**: 18+ (前端)
- **操作系统**: Windows 10/11、macOS、Linux

### 后端启动

```bash
# 克隆仓库
git clone https://github.com/username/interview_system.git
cd interview_system

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/macOS

# 安装后端
pip install -e ".[api]"

# 启动API服务器
uvicorn interview_system.api.main:app --reload --port 8000
```

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

**访问地址:**
- 前端: http://localhost:5173
- API文档: http://localhost:8000/docs

---

## 架构设计

```
interview_system/
├── src/interview_system/
│   ├── api/                  # FastAPI REST API
│   │   ├── main.py           # 应用入口
│   │   ├── routes/           # 路由端点
│   │   └── schemas/          # Pydantic模型
│   ├── core/                 # 业务逻辑
│   ├── services/             # 会话管理
│   ├── data/                 # 数据层
│   └── integrations/         # LLM集成
├── frontend/                 # React SPA
│   ├── src/
│   │   ├── components/       # UI组件
│   │   │   ├── chat/         # Chatbot, MessageBubble
│   │   │   ├── layout/       # Layout, Header, Sidebar
│   │   │   └── common/       # ThemeProvider, CommandPalette
│   │   ├── stores/           # Zustand状态
│   │   ├── hooks/            # TanStack Query hooks
│   │   ├── services/         # API客户端
│   │   └── types/            # TypeScript类型
│   └── package.json
└── llmdoc/                   # LLM文档
```

---

## 技术栈

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 19.2 | UI框架 |
| TypeScript | 5.9 | 类型安全 |
| Vite | 7.3 | 构建工具 |
| ShadcnUI | latest | 组件库 |
| Tailwind CSS | 3.4 | 样式系统 |
| Zustand | 5.0 | 状态管理 |
| TanStack Query | 5.90 | 数据获取 |

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 运行时 |
| FastAPI | 0.110+ | REST API |
| SQLite | - | 数据库 |
| Pydantic | 2.0+ | 数据验证 |

---

## API端点

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/session/start` | 创建会话 |
| GET | `/api/session/{id}` | 获取会话 |
| POST | `/api/session/{id}/message` | 发送消息 |
| POST | `/api/session/{id}/undo` | 撤销交换 |
| POST | `/api/session/{id}/skip` | 跳过问题 |
| POST | `/api/session/{id}/restart` | 重置会话 |
| GET | `/api/session/{id}/stats` | 获取统计 |

---

## 配置说明

### 环境变量

```ini
# 后端 (.env)
API_PROVIDER=deepseek
API_KEY=your_api_key_here
API_MODEL=deepseek-chat

# 前端 (.env)
VITE_API_URL=http://localhost:8000/api
```

### API服务商

| 服务商 | 模型 | 网站 |
|--------|------|------|
| DeepSeek | `deepseek-chat` | [platform.deepseek.com](https://platform.deepseek.com/) |
| OpenAI | `gpt-3.5-turbo` | [platform.openai.com](https://platform.openai.com/) |
| 通义千问 | `qwen-turbo` | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com/) |
| 智谱GLM | `glm-4-flash` | [open.bigmodel.cn](https://open.bigmodel.cn/) |
| 文心一言 | `ernie-3.5-8k` | [qianfan.baidubce.com](https://qianfan.baidubce.com/) |

---

## 开发指南

### 运行测试

```bash
# 前端测试
cd frontend && npm test

# 后端测试
pytest -q
```

### 生产构建

```bash
# 前端
cd frontend && npm run build

# 输出: frontend/dist/
```

---

## 设计系统

### 色彩

| Token | 浅色 | 深色 |
|-------|------|------|
| 背景 | `#F5F7FA` | `#0F172A` |
| 卡片 | `#FFFFFF` | `#1E293B` |
| 主色 | `#7C3AED` | `#7C3AED` |
| 次要 | `#64748B` | `#94A3B8` |

### 间距

8px网格系统: `4px`, `8px`, `16px`, `24px`, `32px`

### 效果

- 卡片阴影: `0 1px 3px rgba(0,0,0,0.05)`
- 玻璃拟态: `backdrop-filter: blur(10px)`
- 悬停上浮: `transform: translateY(-2px)`

---

## 许可证

MIT License

---

## 贡献指南

欢迎贡献代码
