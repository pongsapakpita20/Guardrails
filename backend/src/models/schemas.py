from pydantic import BaseModel
from typing import Optional

class ConfigSwitches(BaseModel):
    violent_check: bool = True
    crime_check: bool = True
    sex_check: bool = True
    child_check: bool = True
    self_harm_check: bool = True
    hate_check: bool = True
    pii_check: bool = False
    off_topic_check: bool = False

class ChatRequest(BaseModel):
    message: str
    config: ConfigSwitches

class ChatResponse(BaseModel):
    status: str
    response: str
    violation: Optional[str] = None
    reason: Optional[str] = None