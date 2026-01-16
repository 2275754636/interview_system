"""Message schemas"""

from pydantic import BaseModel, Field
from typing import Literal


class MessageCreate(BaseModel):
    text: str = Field(..., min_length=1, description="User message text")


class MessageResponse(BaseModel):
    id: str
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: int

    class Config:
        json_schema_extra = {
            "example": {
                "id": "msg_abc123",
                "role": "assistant",
                "content": "请描述一下您的教学理念",
                "timestamp": 1705392000000
            }
        }
