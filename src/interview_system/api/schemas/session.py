"""Session schemas"""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Literal

from interview_system.api.schemas.message import MessageResponse


class SessionCreate(BaseModel):
    user_name: Optional[str] = Field(
        None, min_length=1, description="用户显示名", examples=["访谈者_001"]
    )
    topics: Optional[List[str]] = Field(
        None,
        min_length=1,
        description="指定话题名称列表（可选）",
        examples=[["学校-德育"]],
    )

    @field_validator("user_name")
    @classmethod
    def _validate_user_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("user_name 不能为空")
        return v

    @field_validator("topics")
    @classmethod
    def _validate_topics(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None
        cleaned = [t.strip() for t in v if isinstance(t, str) and t.strip()]
        if not cleaned:
            raise ValueError("topics 不能为空")
        return cleaned


class SessionResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "abc12345",
                "status": "active",
                "current_question": 1,
                "total_questions": 10,
                "created_at": 1705392000000,
                "user_name": "访谈者_abc12345",
            }
        }
    )

    id: str
    status: Literal["idle", "active", "completed"]
    current_question: int = Field(..., description="当前题号（从 0 开始）")
    total_questions: int = Field(..., description="总题数")
    created_at: int = Field(..., description="创建时间（毫秒时间戳）")
    user_name: str = Field(..., description="用户显示名")


class StartSessionResponse(BaseModel):
    """启动会话响应（包含首批 messages，减少一次额外 RTT）。"""

    session: SessionResponse
    messages: List[MessageResponse]


class SessionStats(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_messages": 24,
                "user_messages": 12,
                "assistant_messages": 12,
                "average_response_time": 2.5,
                "duration_seconds": 1800,
            }
        }
    )

    total_messages: int = Field(..., description="总消息数")
    user_messages: int = Field(..., description="用户消息数")
    assistant_messages: int = Field(..., description="助手消息数")
    average_response_time: float = Field(..., description="平均响应时间（秒，估算）")
    duration_seconds: int = Field(..., description="会话持续时间（秒）")
