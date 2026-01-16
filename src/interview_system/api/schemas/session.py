"""Session schemas"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class SessionCreate(BaseModel):
    user_name: Optional[str] = Field(None, description="User display name")
    topics: Optional[List[str]] = Field(None, description="Specific topics to cover")


class SessionResponse(BaseModel):
    id: str
    status: Literal["idle", "active", "completed"]
    current_question: int
    total_questions: int
    created_at: int
    user_name: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "abc12345",
                "status": "active",
                "current_question": 1,
                "total_questions": 10,
                "created_at": 1705392000000,
                "user_name": "访谈者_abc12345"
            }
        }


class SessionStats(BaseModel):
    total_messages: int
    user_messages: int
    assistant_messages: int
    average_response_time: float
    duration_seconds: int

    class Config:
        json_schema_extra = {
            "example": {
                "total_messages": 24,
                "user_messages": 12,
                "assistant_messages": 12,
                "average_response_time": 2.5,
                "duration_seconds": 1800
            }
        }
