# Interview System REST API

Interview System 的 FastAPI 后端。

## 安装

```bash
pip install -e ".[dev,api]"
```

## 快速开始

### 开发服务

```bash
uvicorn interview_system.api.main:app --reload --port 8000
```

或使用运行脚本：

```bash
python -m interview_system.api.run
```

### API 文档

启动后可访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

## 接口列表

### Session 管理

- `POST /api/session/start` - 创建新会话
- `GET /api/session/{session_id}` - 获取会话信息
- `GET /api/session/{session_id}/messages` - 获取消息列表
- `POST /api/session/{session_id}/message` - 发送用户消息
- `POST /api/session/{session_id}/undo` - 撤销上一轮对话
- `POST /api/session/{session_id}/skip` - 跳过当前问题
- `POST /api/session/{session_id}/restart` - 重置会话
- `GET /api/session/{session_id}/stats` - 获取统计信息
- `DELETE /api/session/{session_id}` - 删除会话

### 公网分享

- `GET /api/public-url` - 获取前端公网 URL 状态（由启动器写入）

## 示例

### 启动会话

```bash
curl -X POST http://localhost:8000/api/session/start \
  -H "Content-Type: application/json" \
  -d '{"user_name": "测试用户", "topics": null}'
```

响应示例：
```json
{
  "session": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "active",
    "current_question": 0,
    "total_questions": 10,
    "created_at": 1705392000000,
    "user_name": "测试用户"
  },
  "messages": [
    {
      "id": "msg_abc123",
      "role": "assistant",
      "content": "请描述一下您的教学理念",
      "timestamp": 1705392000000
    }
  ]
}
```

### 发送消息

```bash
curl -X POST http://localhost:8000/api/session/550e8400-e29b-41d4-a716-446655440000/message \
  -H "Content-Type: application/json" \
  -d '{"text": "我认为教学应该以学生为中心"}'
```

响应示例：
```json
{
  "id": "msg_xyz789",
  "role": "assistant",
  "content": "能否详细说明您如何在实际教学中体现以学生为中心？",
  "timestamp": 1705392060000
}
```

## 目录结构

```
src/interview_system/api/
├── __init__.py
├── main.py          # FastAPI 应用工厂与路由挂载
├── run.py           # 服务启动入口
├── deps.py          # 依赖注入
├── routes/
│   ├── __init__.py
│   ├── session.py   # Session 路由
│   ├── interview.py # Interview 路由
│   └── health.py    # 健康检查
└── schemas/
    ├── __init__.py
    ├── common.py    # 统一错误响应
    ├── session.py   # Session 相关模型
    └── message.py   # Message 相关模型
```

## App Factory

`create_app(settings)` 支持在测试中注入不同的 `Settings`。

## CORS 配置

默认仅允许本地开发源：
- 通过 `CORS_ORIGINS`（逗号分隔）显式配置允许的 origins；未配置时会 fallback 到本地开发地址（见 `src/interview_system/api/main.py`）。

公网/隧道域名来源默认关闭，需显式开启：
- `CORS_ALLOWED_HOST_SUFFIXES`（逗号分隔），例如：`.trycloudflare.com,.ngrok-free.app,.ngrok.io`
- 开启后会构造 `allow_origin_regex` 以允许对应后缀的 `https://{subdomain}.{suffix}` 来源

提示：使用 `python start.py --public` 启动时，启动器会为后端进程自动注入 `CORS_ALLOWED_HOST_SUFFIXES`。
