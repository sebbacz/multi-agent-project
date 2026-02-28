from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional
import uuid

class Turn(BaseModel):
    idx: int
    t: Optional[str] = None
    speaker: str
    text: str

class Transcript(BaseModel):
    meeting_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    meeting_date: date
    participants: List[str]
    turns: List[Turn]
