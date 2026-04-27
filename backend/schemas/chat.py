from typing import List, Optional

from pydantic import BaseModel


class Action(BaseModel):
    label: str
    action: str


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    actions: Optional[List[Action]] = None
