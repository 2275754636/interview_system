<div align="center">

# 访谈系统

**AI驱动的五育并举教育评估访谈平台**

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
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
- 后台监管仪表盘，支持数据分析与导出 (CSV/JSON/XLSX)
- 公网URL分享，支持二维码扫描 (cloudflared/ngrok)
- 外部化配置 (基于YAML的关键词配置)

</td>
<td width="50%">

**v3.0 现代化UI**
- React 19 + TypeScript + ShadcnUI
- Bento Grid 便当盒布局
- 深色模式支持
- 命令面板 (Ctrl+K)
- 玻璃拟态效果
- 微交互动画
- PWA支持 (离线可用)
- 性能监控 (Web Vitals)

</td>
</tr>
</table>

---

## 快速开始

### 环境要求

- **Python**: 3.11+
- **Node.js**: 18+

### 一键启动

```bash
git clone https://github.com/username/interview_system.git
cd interview_system
python start.py
```

自动检测环境、安装依赖、启动所有服务。

#### 首次运行配置

首次运行时，系统会交互式提示：
- 选择 AI 提供商（deepseek/openai/qwen/glm/ernie）
- 输入 API 密钥（隐藏输入）
- 输入 Secret Key（仅文心一言需要，隐藏输入）
- 可选：覆盖默认模型（按 Enter 使用默认值）

**API 验证：**
- 系统在启动前验证您的 API 密钥
- 如果验证失败，系统自动回退到预设问题模式
- 即使没有有效的 API 密钥，您仍可使用访谈系统（仅限预设问题）

**后台监管 Token：**
- 系统启动时自动生成 32 位随机密码
- Token 在终端显著位置显示（启动完成后）
- 每次启动生成新 Token，确保安全性

**访问地址:**
- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 后台监管仪表盘: http://localhost:5173/#admin/overview

按 `Ctrl+C` 停止所有服务。

### 公网访问 (隧道)

```bash
python start.py --public
```

通过 cloudflared/ngrok 暴露服务，支持远程访问。

**依赖:**
- [Cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/) (推荐，无需注册)
- [Ngrok](https://ngrok.com/download) (备选)

**功能特性:**
- 隧道就绪时打印公网URL
- 终端显示ASCII二维码，方便移动设备扫描
- 前端显示二维码对话框（点击标题栏分享图标）
- 隧道状态持久化至 `.public_url_state.json`

**输出:**
```
前端 公网: https://abc123.trycloudflare.com
后端 公网: https://def456.trycloudflare.com
```

<details>
<summary>手动启动</summary>

```bash
# 后端
pip install -e ".[api]"
uvicorn interview_system.api.main:app --reload --port 8000

# 前端 (新终端)
cd frontend && npm install && npm run dev
```

</details>

---

## 架构设计

```
interview_system/
├── src/interview_system/
│   ├── api/                  # FastAPI REST API
│   │   ├── main.py           # 应用入口
│   │   ├── routes/           # 路由端点
│   │   └── schemas/          # Pydantic模型
│   ├── application/          # 应用层（用例）
│   ├── domain/               # 领域层（实体/服务）
│   ├── infrastructure/       # 基础设施（DB/缓存/外部）
│   ├── config/               # 配置与日志
│   ├── core/                 # 数据/题库（如 questions）
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
| vite-plugin-pwa | 1.2 | PWA支持 |
| workbox-window | 7.4 | Service Worker |
| web-vitals | 5.1 | 性能指标 |

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 运行时 |
| FastAPI | 0.110+ | REST API |
| SQLite | - | 数据库 |
| Pydantic | 2.0+ | 数据验证 |

---

## API端点

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/session/start` | 创建会话 |
| GET | `/api/session/{id}` | 获取会话 |
| GET | `/api/session/{id}/messages` | 获取消息 |
| POST | `/api/session/{id}/message` | 发送消息 |
| POST | `/api/session/{id}/undo` | 撤销交换 |
| POST | `/api/session/{id}/skip` | 跳过问题 |
| POST | `/api/session/{id}/restart` | 重置会话 |
| GET | `/api/session/{id}/stats` | 获取统计 |
| DELETE | `/api/session/{id}` | 删除会话 |

### 后台监管（仪表盘）

通过 `ADMIN_TOKEN` 保护（请求头 `X-Admin-Token`）。若 `ADMIN_TOKEN` 为空，后台监管接口将返回 `404`。

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/admin/overview` | 指标概览 + 时间序列 |
| GET | `/api/admin/sessions` | 会话列表（过滤 + 分页） |
| GET | `/api/admin/search` | 搜索对话记录 |
| GET | `/api/admin/export` | 导出 CSV/JSON/XLSX |

---

## 配置说明

### 环境变量

```ini
# 后端 (.env)
API_PROVIDER=deepseek  # deepseek/openai/qwen/zhipu/baidu
API_KEY=your_api_key_here
API_MODEL=deepseek-chat
API_SECRET_KEY=your_secret_key_here  # 仅百度需要
DATABASE_URL=sqlite+aiosqlite:///./interview_data.db
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:5173
ADMIN_TOKEN=auto_generated  # 启动时自动生成，无需手动配置

# 前端 (.env)
VITE_API_URL=http://localhost:8000/api
```

**注意：**
- `glm` 在 `.env` 中存储为 `API_PROVIDER=zhipu`
- `ernie` 在 `.env` 中存储为 `API_PROVIDER=baidu`
- 设置 `API_KEY=""` (空值) 将强制使用预设问题（无AI追问）
- `ADMIN_TOKEN` 在每次启动时自动生成，无需手动配置

### API服务商

| 服务商 | 模型 | 网站 |
|--------|------|------|
| DeepSeek | `deepseek-chat` | [platform.deepseek.com](https://platform.deepseek.com/) |
| OpenAI | `gpt-3.5-turbo` | [platform.openai.com](https://platform.openai.com/) |
| 通义千问 | `qwen-turbo` | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com/) |
| 智谱GLM | `glm-4-flash` | [open.bigmodel.cn](https://open.bigmodel.cn/) |
| 文心一言 | `ernie-3.5-8k` | [qianfan.baidubce.com](https://qianfan.baidubce.com/) |

### 访谈关键词配置

深度评分关键词已外部化至 `config/interview_keywords.yaml`：

```yaml
depth_keywords:
  - "具体"
  - "例如"
  - "因为"
  # ... 更多关键词
```

系统自动加载此文件，如果文件不存在则回退到硬编码默认值。您可以自定义关键词而无需修改代码。

---

## 故障排除

### 文本输入被禁用

**症状：** 无法在消息输入框中输入文字。

**原因：** 会话未启动，或正在等待第一个问题。

**解决方案：**
- 点击"快速访谈"按钮，等待第一个问题出现。

### API 验证失败

**症状：** 启动时显示警告消息：
```
⚠ API 验证失败: [错误详情]
  回退模式: 使用预设问题
```

**原因：** API 密钥无效、网络问题或提供商服务不可用。

**解决方案：**
- 检查 `.env` 文件中的 `API_PROVIDER`、`API_KEY`、`API_SECRET_KEY`（百度需要）
- 重新运行 `python start.py` 重新配置
- 或强制使用预设模式：设置 `API_KEY=""`

---

## 开发指南

```bash
# 测试
cd frontend && npm test    # 前端
pytest -q                  # 后端

# 构建
cd frontend && npm run build
```

---

## 许可证

MIT
