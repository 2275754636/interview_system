# Interview System REST API

FastAPI backend for the interview system.

## Installation

```bash
pip install -e ".[api]"
```

## Quick Start

### Development Server

```bash
uvicorn interview_system.api.main:app --reload --port 8000
```

Or use the run script:

```bash
python -m interview_system.api.run
```

### API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## Endpoints

### Session Management

- `POST /api/session/start` - Create new interview session
- `GET /api/session/{session_id}` - Get session details
- `GET /api/session/{session_id}/messages` - Get all messages
- `POST /api/session/{session_id}/message` - Send user message
- `POST /api/session/{session_id}/undo` - Undo last exchange
- `POST /api/session/{session_id}/skip` - Skip current question
- `POST /api/session/{session_id}/restart` - Reset session
- `GET /api/session/{session_id}/stats` - Get statistics
- `DELETE /api/session/{session_id}` - Delete session

## Example Usage

### Start Session

```bash
curl -X POST http://localhost:8000/api/session/start \
  -H "Content-Type: application/json" \
  -d '{"user_name": "测试用户"}'
```

Response:
```json
{
  "id": "abc12345",
  "status": "active",
  "current_question": 0,
  "total_questions": 10,
  "created_at": 1705392000000,
  "user_name": "测试用户"
}
```

### Send Message

```bash
curl -X POST http://localhost:8000/api/session/abc12345/message \
  -H "Content-Type: application/json" \
  -d '{"text": "我认为教学应该以学生为中心"}'
```

Response:
```json
{
  "id": "msg_xyz789",
  "role": "assistant",
  "content": "能否详细说明您如何在实际教学中体现以学生为中心？",
  "timestamp": 1705392060000
}
```

## Architecture

```
src/interview_system/api/
├── __init__.py
├── main.py          # FastAPI app
├── run.py           # Server launcher
├── deps.py          # Dependency injection
├── routes/
│   ├── __init__.py
│   └── session.py   # Session endpoints
└── schemas/
    ├── __init__.py
    ├── session.py   # Session models
    └── message.py   # Message models
```

## Integration

The API integrates with existing core modules:
- `interview_system.services.session_manager.SessionManager`
- `interview_system.core.interview_engine.InterviewEngine`

No changes to core logic required.

## CORS Configuration

Configured for frontend development:
- http://localhost:5173 (Vite)
- http://localhost:3000 (Alternative)

Update `main.py` for production origins.
